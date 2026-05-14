"""Main application window."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSplitter, QTextEdit, QMessageBox, QLabel, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont
import re
from pathlib import Path
from typing import Optional
import sys
import os
import subprocess

from .chat_widget import ChatWidget
from .sidebar import ConversationSidebar
from .config_dialog import ConfigDialog
from .template_dialog import TemplateDialog
from .settings_dialog import SettingsDialog
from .stt_dialog import STTDialog
from .styles import get_stylesheet

from ..models.openvino_wrapper import OpenVINOWrapper
from ..models.model_manager import ModelManager
from ..models.chat_manager import ChatManager
from ..storage.json_backend import JSONStorage
from ..templates.template_manager import TemplateManager
from ..utils.settings import SettingsManager
from ..utils.logger import setup_logger
from ..utils.constants import WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH, Device

class GenerationWorker(QThread):
    """Worker thread for model inference."""
    
    # Signals
    chunk_received = pyqtSignal(str)
    generation_complete = pyqtSignal(str)
    generation_error = pyqtSignal(str)
    
    def __init__(self, model: OpenVINOWrapper, prompt: str):
        """
        Initialize generation worker.
        
        Args:
            model: OpenVINO model wrapper
            prompt: Prompt to generate from
        """
        super().__init__()
        self.model = model
        self.prompt = prompt
    
    def run(self) -> None:
        """Run the generation in the background."""
        try:
            def callback(chunk: str) -> None:
                """Callback for streaming chunks."""
                self.chunk_received.emit(chunk)
            
            response = self.model.generate_streaming(self.prompt, callback)
            self.generation_complete.emit(response)
        
        except Exception as e:
            logger.error(f"Generation error: {e}")
            self.generation_error.emit(str(e))


logger = None

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("OpenVINO GenAI Chat")
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.storage = JSONStorage()
        self.chat_manager = ChatManager(self.storage)
        self.template_manager = TemplateManager()
        
        # Get pre-initialized model from global ModelManager
        model_manager = ModelManager.get_instance()
        self.model: Optional[OpenVINOWrapper] = model_manager.get_model()
        
        if self.model:
            logger.info("✓ Using pre-initialized model from ModelManager")
        else:
            logger.warning("⚠ Model not initialized by ModelManager")
            if model_manager.get_error():
                logger.error(f"Model init error: {model_manager.get_error()}")
        
        self.generation_worker: Optional[GenerationWorker] = None
        self.is_generating = False
        
        self.setup_ui()
        self.apply_theme(self.settings_manager.get("theme", "dark"))
        
        # Load conversations and update UI
        self.post_init_setup()
    
    def post_init_setup(self) -> None:
        """Setup that runs after window is displayed."""
        try:
            if self.model:
                use_thinking = self.settings_manager.get_use_thinking()
                self.chat_manager.use_thinking = use_thinking
                self.thinking_btn.setChecked(use_thinking)
                self.toggle_thinking_mode()  # sync button text with checked state
                self.update_status("✓ Ready - Model loaded")
                
                try:
                    self.load_conversations()
                    logger.info("Conversations loaded successfully")
                except Exception as e:
                    logger.error(f"Error loading conversations: {e}")
                    self.update_status("Ready (failed to load conversations)")
            else:
                self.update_status("⚠ Model not loaded - Configure in Settings")
        except Exception as e:
            logger.error(f"Error in post_init_setup: {e}", exc_info=True)
            self.update_status(f"Error: {str(e)[:40]}...")
    
    def setup_ui(self) -> None:
        """Set up the main window UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 8, 10, 8)
        toolbar_layout.setSpacing(8)
        
        # Thinking mode toggle button
        self.thinking_btn = QPushButton("/no_think")
        self.thinking_btn.setCheckable(True)
        self.thinking_btn.setChecked(False)
        self.thinking_btn.setMaximumWidth(100)
        self.thinking_btn.setObjectName("toggleButton")
        self.thinking_btn.clicked.connect(self.toggle_thinking_mode)
        toolbar_layout.addWidget(self.thinking_btn)
        
        toolbar_layout.addSpacing(10)
        
        # Config button
        config_btn = QPushButton("⚙ Config")
        config_btn.clicked.connect(self.open_config_dialog)
        toolbar_layout.addWidget(config_btn)
        
        # Templates button
        templates_btn = QPushButton("📋 Templates")
        templates_btn.clicked.connect(self.open_template_dialog)
        toolbar_layout.addWidget(templates_btn)
        
        # Settings button
        settings_btn = QPushButton("⚡ Settings")
        settings_btn.clicked.connect(self.open_settings_dialog)
        toolbar_layout.addWidget(settings_btn)
        
        # STT button
        stt_btn = QPushButton("🎙️ STT")
        stt_btn.clicked.connect(self.open_stt_dialog)
        toolbar_layout.addWidget(stt_btn)
        
        toolbar_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px;")
        toolbar_layout.addWidget(self.status_label)
        
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("toolbarWidget")
        toolbar_widget.setLayout(toolbar_layout)
        main_layout.addWidget(toolbar_widget)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ConversationSidebar()
        self.sidebar.setObjectName("sidebarWidget")
        self.sidebar.conversation_selected.connect(self.on_conversation_selected)
        self.sidebar.new_conversation_clicked.connect(self.on_new_conversation)
        self.sidebar.conversation_deleted.connect(self.on_conversation_deleted)
        self.sidebar.conversation_renamed.connect(self.on_conversation_renamed)
        self.sidebar.setMaximumWidth(SIDEBAR_WIDTH)
        content_layout.addWidget(self.sidebar)
        
        # Chat area
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat widget
        self.chat_widget = ChatWidget()
        chat_layout.addWidget(self.chat_widget)
        
        # Input area
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)
        
        # Input text edit
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your message here... (Shift+Enter for new line, Enter to send)")
        self.input_text.setMaximumHeight(100)
        input_layout.addWidget(self.input_text)
        
        # Input buttons
        input_buttons_layout = QHBoxLayout()
        input_buttons_layout.setSpacing(8)
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy Last Response")
        self.copy_btn.clicked.connect(self.copy_last_response)
        input_buttons_layout.addWidget(self.copy_btn)
        
        # Send button
        self.send_btn = QPushButton("▶ Send")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setMinimumHeight(36)
        input_buttons_layout.addWidget(self.send_btn)
        
        # Cancel button (hidden by default)
        self.cancel_btn = QPushButton("✕ Cancel")
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.setVisible(False)
        input_buttons_layout.addWidget(self.cancel_btn)
        
        input_layout.addLayout(input_buttons_layout)
        
        input_widget = QWidget()
        input_widget.setObjectName("inputWidget")
        input_widget.setLayout(input_layout)
        chat_layout.addWidget(input_widget)
        
        chat_area = QWidget()
        chat_area.setLayout(chat_layout)
        content_layout.addWidget(chat_area, 1)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)
        
        central_widget.setLayout(main_layout)
        
        # Connect keyboard shortcuts
        self.input_text.keyPressEvent = self.on_input_key_press
    
    def on_input_key_press(self, event) -> None:
        """Handle keyboard input in text edit."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                # Shift+Enter: new line
                self.input_text.insertPlainText("\n")
            else:
                # Enter: send message
                self.send_message()
        else:
            # Default behavior
            QTextEdit.keyPressEvent(self.input_text, event)
    
    def toggle_thinking_mode(self) -> None:
        """Toggle between /think and /no_think modes."""
        use_thinking = self.thinking_btn.isChecked()
        self.chat_manager.set_use_thinking(use_thinking)
        
        label = "/think" if use_thinking else "/no_think"
        self.thinking_btn.setText(label)
        logger.info(f"Thinking mode toggled: {use_thinking}")
    

    
    def load_conversations(self) -> None:
        """Load conversations from storage."""
        try:
            conversations = self.chat_manager.list_conversations()
            self.sidebar.load_conversations(conversations)
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
    
    def on_new_conversation(self) -> None:
        """Handle new conversation button click."""
        if not self.model:
            self.update_status("❌ Model not initialized - Configure in Settings")
            return
        
        try:
            self.chat_manager.new_conversation(
                model_name=str(self.settings_manager.get_model_path()),
                model_device=self.settings_manager.get_device().value,
                max_tokens=self.settings_manager.get_max_tokens(),
                use_thinking=self.chat_manager.use_thinking,
            )
            
            self.chat_widget.clear()
            self.input_text.clear()
            self.update_status("New conversation started")
            self.load_conversations()
            
            # Focus on the new conversation in the sidebar
            new_id = self.chat_manager.current_conversation_id
            if new_id:
                self.sidebar.select_conversation(new_id)
            
            self.input_text.setFocus()
        
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            self.update_status(f"❌ Failed to create conversation: {str(e)[:40]}...")
    
    def on_conversation_selected(self, conversation_id: str) -> None:
        """Handle conversation selection from sidebar."""
        try:
            if self.chat_manager.load_conversation(conversation_id):
                self.chat_widget.clear()
                
                # Load and display messages
                for msg in self.chat_manager.get_conversation_messages():
                    is_user = msg["role"] == "user"
                    self.chat_widget.add_message(msg["content"], is_user)
                
                # Update thinking mode from conversation
                self.thinking_btn.setChecked(self.chat_manager.use_thinking)
                self.toggle_thinking_mode()
                
                self.input_text.clear()
                self.update_status(f"Loaded conversation: {conversation_id[:8]}...")
        
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            self.update_status(f"❌ Failed to load conversation: {str(e)[:40]}...")
    
    def on_conversation_deleted(self, conversation_id: str) -> None:
        """Handle conversation deletion."""
        try:
            self.chat_manager.delete_conversation(conversation_id)
            self.load_conversations()
            self.update_status("Conversation deleted")
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
    
    def on_conversation_renamed(self, conversation_id: str, new_title: str) -> None:
        """Handle conversation rename."""
        try:
            self.chat_manager.rename_conversation(conversation_id, new_title)
            self.load_conversations()
            self.update_status(f"Conversation renamed to: {new_title}")
        except Exception as e:
            logger.error(f"Failed to rename conversation: {e}")
    
    def send_message(self) -> None:
        """Send the message to the model."""
        if self.is_generating:
            self.update_status("⏳ Busy - Please wait for current generation to complete")
            return
        
        if not self.model:
            self.update_status("❌ Model not initialized - Configure in Settings")
            return
        
        prompt = self.input_text.toPlainText().strip()
        if not prompt:
            return
        
        # Ensure there's an active conversation
        if not self.chat_manager.current_conversation_id:
            self.on_new_conversation()
            if not self.chat_manager.current_conversation_id:
                return
        
        try:
            # Add user message
            self.chat_manager.add_user_message(prompt)
            self.chat_widget.add_message(prompt, is_user=True)
            self.input_text.clear()
            
            # Format prompt with thinking directive
            formatted_prompt = self.chat_manager.format_prompt(prompt, self.chat_manager.use_thinking)
            
            # Start generation
            self.is_generating = True
            self.send_btn.setVisible(False)
            self.cancel_btn.setVisible(True)
            self.input_text.setEnabled(False)
            self.update_status("Generating response...")
            
            # Start model inference in worker thread
            self.chat_widget.start_streaming_message(is_user=False)
            
            self.generation_worker = GenerationWorker(self.model, formatted_prompt)
            self.generation_worker.chunk_received.connect(self.on_generation_chunk)
            self.generation_worker.generation_complete.connect(self.on_generation_complete)
            self.generation_worker.generation_error.connect(self.on_generation_error)
            self.generation_worker.start()
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.is_generating = False
            self.send_btn.setVisible(True)
            self.cancel_btn.setVisible(False)
            self.input_text.setEnabled(True)
            self.update_status(f"❌ Error: {str(e)[:40]}...")
    
    def on_generation_chunk(self, chunk: str) -> None:
        """Handle receiving a chunk of generated text."""
        self.chat_widget.append_streaming_text(chunk)
    
    def on_generation_complete(self, response: str) -> None:
        """Handle generation completion."""
        self.is_generating = False
        self.send_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.input_text.setEnabled(True)
        
        # Save the complete message
        self.chat_widget.finish_streaming_message()
        self.chat_manager.add_assistant_message(response)
        
        self.update_status("Response complete")
        logger.info("Generation complete")
    
    def on_generation_error(self, error: str) -> None:
        """Handle generation error."""
        self.is_generating = False
        self.send_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.input_text.setEnabled(True)
        
        logger.error(f"Generation error: {error}")
        self.update_status(f"❌ Generation error: {error[:40]}...")
    
    def cancel_generation(self) -> None:
        """Cancel the current generation without blocking the UI thread."""
        if self.model:
            self.model.stop_generation()
        
        if self.generation_worker and self.generation_worker.isRunning():
            # Give the worker the configured time to honour the stop flag gracefully
            cancel_wait_ms = self.settings_manager.get("cancel_wait_ms", 3000)
            finished = self.generation_worker.wait(cancel_wait_ms)
            if not finished:
                # Last resort: force terminate (avoids UI freeze)
                logger.warning("Generation worker did not stop in time – terminating forcefully")
                self.generation_worker.terminate()
                self.generation_worker.wait(1000)
        
        self.is_generating = False
        self.send_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.input_text.setEnabled(True)
        
        self.update_status("Generation cancelled")
    
    def copy_last_response(self) -> None:
        """Copy the last assistant response to clipboard."""
        last_response = self.chat_widget.get_last_assistant_message()
        
        if not last_response:
            self.update_status("ℹ️ No response to copy")
            return
            
        # Strip <think> blocks
        clean_text = re.sub(r'<think>.*?</think>', '', last_response, flags=re.DOTALL).strip()
        
        clipboard = QApplication.clipboard()
        clipboard.setText(clean_text)
        
        self.update_status("✓ Response copied to clipboard")
    
    def open_config_dialog(self) -> None:
        """Open the configuration dialog."""
        dialog = ConfigDialog(
            current_model_path=str(self.settings_manager.get_model_path()),
            current_device=self.settings_manager.get_device().value,
            current_max_tokens=self.settings_manager.get_max_tokens(),
            current_use_thinking=self.chat_manager.use_thinking,
            current_cancel_wait_ms=self.settings_manager.get("cancel_wait_ms", 5000),
            parent=self,
        )
        
        dialog.settings_applied.connect(self.on_config_applied)
        dialog.exec_()  # Modal dialog
    
    def on_config_applied(self, model_path: str, device: str, max_tokens: int, use_thinking: bool, cancel_wait_ms: int) -> None:
        """Handle configuration changes."""
        try:
            # Update settings
            self.settings_manager.set("model_path", model_path)
            self.settings_manager.set("device", device)
            self.settings_manager.set("max_new_tokens", max_tokens)
            self.settings_manager.set("cancel_wait_ms", cancel_wait_ms)
            self.settings_manager.set_use_thinking(use_thinking)
            
            self.update_status("Settings saved. Shutdown required to apply new model.")
            
            reply = QMessageBox.question(
                self, 
                "Shutdown Required",
                "Model configuration changed. The application needs to close to load the new settings. Close now?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.shutdown_app()
        
        except Exception as e:
            logger.error(f"Error applying configuration: {e}")
            self.update_status(f"❌ Configuration error: {str(e)[:50]}")
    
    def open_template_dialog(self) -> None:
        """Open the template dialog."""
        dialog = TemplateDialog(self.template_manager, self)
        dialog.template_applied.connect(self.on_template_applied)
        dialog.exec_()  # Modal dialog
    
    def on_template_applied(self, prompt: str) -> None:
        """Handle template prompt insertion."""
        self.input_text.setPlainText(prompt)
        self.input_text.setFocus()
        self.update_status("Template applied - review and send")
    
    def open_settings_dialog(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(
            current_theme=self.settings_manager.get("theme", "dark"),
            parent=self,
        )
        
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec_()  # Modal dialog
    
    def on_settings_changed(self, key: str, value) -> None:
        """Handle settings changes."""
        if key == "theme":
            self.settings_manager.set(key, value)
            self.settings_manager.save()
            self.apply_theme(value)
    
    def open_stt_dialog(self) -> None:
        """Open the Speech-to-Text dialog."""
        dialog = STTDialog(self)
        dialog.exec_()
    
    def apply_theme(self, theme: str) -> None:
        """Apply a theme to the application."""
        stylesheet = get_stylesheet(theme)
        QApplication.instance().setStyle('Fusion')
        QApplication.instance().setStyleSheet(stylesheet)
        self.chat_widget.set_theme(theme)
        logger.info(f"Theme applied: {theme}")
    
    def shutdown_app(self) -> None:
        """Shutdown the application so the user can restart it."""
        logger.info("Shutting down application for restart...")
        
        # Save settings one last time
        self.settings_manager.save()
        
        # Just quit
        QApplication.quit()
    
    def update_status(self, message: str) -> None:
        """Update the status label."""
        self.status_label.setText(message)
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        try:
            logger.info("Window close event received")
            # Save settings
            self.settings_manager.save()
            logger.info("Settings saved, accepting close event")
            event.accept()
        except Exception as e:
            logger.error(f"Error closing application: {e}", exc_info=True)
            event.accept()

def main(pipe, other_logger):
    """Main entry point for the application."""
    global logger
    logger = other_logger
    logger.info("=" * 70)
    logger.info("APPLICATION STARTUP")
    logger.info("=" * 70)

    try:
        # PHASE 1: Initialize model BEFORE PyQt5 starts
        logger.info("\n[PHASE 1] Initializing OpenVINO model (BEFORE PyQt5)...")
        settings_mgr = SettingsManager()
        model_path = settings_mgr.get_model_path()
        device = settings_mgr.get_device()
        max_tokens = settings_mgr.get_max_tokens()
        
        # Initialize the global ModelManager with the model (without actually initializing the model yet)
        model_mgr = ModelManager.get_instance()
        model_mgr.model = OpenVINOWrapper(model_path, device, max_tokens, dont_initialize_model=True)
        model_mgr.model.pipeline = pipe
        
        # TODO: Add error handling and timeout for model initialization here if needed
        # if not model_mgr.initialize(model_path, device, max_tokens):
        #     logger.warning("Model initialization failed, app will run with degraded functionality")
        
        # PHASE 2: Create PyQt5 application
        logger.info("\n[PHASE 2] Creating PyQt5 application...")
        app = QApplication(sys.argv)
        
        # PHASE 3: Create main window (with pre-loaded model)
        logger.info("\n[PHASE 3] Creating main window...")
        window = MainWindow()
        
        # PHASE 4: Show window
        logger.info("[PHASE 4] Showing main window...")
        window.show()
        
        # Post-init setup
        window.post_init_setup()
        
        # PHASE 5: Start event loop
        logger.info("[PHASE 5] Entering event loop\n")
        logger.info("=" * 70)
        exit_code = app.exec_()
        logger.info("=" * 70)
        logger.info(f"Event loop exited with code: {exit_code}")
        sys.exit(exit_code)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        logger.error("=" * 70)
        sys.exit(1)