"""Speech-to-Text dialog for transcribing audio files."""

import os
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFileDialog, QTextEdit, 
    QProgressBar, QMessageBox, QFrame, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from ..models.stt_manager import STTManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class STTWorker(QThread):
    """Worker thread for STT operations (download and transcription)."""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    new_text = pyqtSignal(str)
    
    def __init__(self, task: str, manager: STTManager, **kwargs):
        super().__init__()
        self.task = task
        self.manager = manager
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.task == "download":
                repo_id = self.kwargs.get("repo_id")
                def progress_cb(p):
                    self.progress.emit(p)
                model_path = self.manager.download_model(repo_id, progress_callback=progress_cb)
                self.finished.emit(model_path)
            elif self.task == "transcribe":
                audio_path = self.kwargs.get("audio_path")
                def streamer_cb(text):
                    # If the pipeline sends raw token IDs (int or list of ints), 
                    # use the manager's tokenizer to decode them.
                    if isinstance(text, (int, list)):
                        tokens = [text] if isinstance(text, int) else text
                        if self.manager.tokenizer:
                            text = self.manager.tokenizer.decode(tokens)
                        else:
                            text = " ".join(str(t) for t in tokens)
                    
                    self.new_text.emit(str(text))
                    return False # False means don't stop
                    
                # Extract inference kwargs
                inference_kwargs = {}
                if self.kwargs.get("language"):
                    inference_kwargs["language"] = self.kwargs["language"]
                if self.kwargs.get("inference_task"):
                    inference_kwargs["task"] = self.kwargs["inference_task"]
                    
                text = self.manager.transcribe(
                    audio_path, 
                    streamer_callback=streamer_cb,
                    **inference_kwargs
                )
                self.finished.emit(text)
            elif self.task == "load":
                model_path = self.kwargs.get("model_path")
                success = self.manager.load_model(model_path)
                self.finished.emit(success)
        except Exception as e:
            logger.error(f"STT worker error: {e}")
            self.error.emit(str(e))

class STTDialog(QDialog):
    """Dialog for Speech-to-Text operations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Speech-to-Text (OpenVINO)")
        self.setMinimumSize(600, 500)
        
        self.manager = STTManager()
        self.worker: Optional[STTWorker] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Model Section ---
        model_group = QVBoxLayout()
        model_label = QLabel("<b>1. Select or Download OpenVINO STT Model</b>")
        model_group.addWidget(model_label)
        
        hf_layout = QHBoxLayout()
        self.model_selector = QComboBox()
        self.model_selector.setEditable(True)
        self.model_selector.setPlaceholderText("Select or type Hugging Face repo ID...")
        self.model_selector.addItem("OpenVINO/whisper-base-int8-ov")
        
        # Add local models
        local_models = self.manager.list_local_models()
        for model in local_models:
            if model["name"] != "OpenVINO/whisper-base-int8-ov":
                self.model_selector.addItem(model["name"])
                
        hf_layout.addWidget(self.model_selector, 1)
        
        self.download_btn = QPushButton("Download / Load")
        self.download_btn.clicked.connect(self.download_model)
        hf_layout.addWidget(self.download_btn)
        model_group.addLayout(hf_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        model_group.addWidget(self.progress_bar)
        
        self.model_status_label = QLabel("Model not loaded")
        self.model_status_label.setStyleSheet("color: #888888; font-size: 10px;")
        model_group.addWidget(self.model_status_label)
        
        layout.addLayout(model_group)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # --- Audio Section ---
        audio_group = QVBoxLayout()
        audio_label = QLabel("<b>2. Select Media File</b> (.mp3, .wav, .m4a, .mp4)")
        audio_group.addWidget(audio_label)
        
        audio_file_layout = QHBoxLayout()
        self.audio_path_input = QLineEdit()
        self.audio_path_input.setPlaceholderText("Select an audio file...")
        self.audio_path_input.setReadOnly(True)
        self.audio_path_input.textChanged.connect(self.update_transcribe_btn_state)
        audio_file_layout.addWidget(self.audio_path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_audio)
        audio_file_layout.addWidget(self.browse_btn)
        audio_group.addLayout(audio_file_layout)
        
        # Language and Task options
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("Language:"))
        self.language_selector = QComboBox()
        # All 99 languages supported by multilingual Whisper models (sorted alphabetically)
        _languages = [
            ("Auto Detect",      ""),
            ("Afrikaans",        "<|af|>"),
            ("Amharic",          "<|am|>"),
            ("Arabic",           "<|ar|>"),
            ("Assamese",         "<|as|>"),
            ("Azerbaijani",      "<|az|>"),
            ("Bashkir",          "<|ba|>"),
            ("Basque",           "<|eu|>"),
            ("Belarusian",       "<|be|>"),
            ("Bengali",          "<|bn|>"),
            ("Bosnian",          "<|bs|>"),
            ("Breton",           "<|br|>"),
            ("Bulgarian",        "<|bg|>"),
            ("Cantonese",        "<|yue|>"),
            ("Catalan",          "<|ca|>"),
            ("Chinese",          "<|zh|>"),
            ("Croatian",         "<|hr|>"),
            ("Czech",            "<|cs|>"),
            ("Danish",           "<|da|>"),
            ("Dutch",            "<|nl|>"),
            ("English",          "<|en|>"),
            ("Estonian",         "<|et|>"),
            ("Faroese",          "<|fo|>"),
            ("Finnish",          "<|fi|>"),
            ("French",           "<|fr|>"),
            ("Galician",         "<|gl|>"),
            ("Georgian",         "<|ka|>"),
            ("German",           "<|de|>"),
            ("Greek",            "<|el|>"),
            ("Gujarati",         "<|gu|>"),
            ("Haitian Creole",   "<|ht|>"),
            ("Hausa",            "<|ha|>"),
            ("Hawaiian",         "<|haw|>"),
            ("Hebrew",           "<|he|>"),
            ("Hindi",            "<|hi|>"),
            ("Hungarian",        "<|hu|>"),
            ("Armenian",         "<|hy|>"),
            ("Icelandic",        "<|is|>"),
            ("Indonesian",       "<|id|>"),
            ("Italian",          "<|it|>"),
            ("Japanese",         "<|ja|>"),
            ("Javanese",         "<|jw|>"),
            ("Kannada",          "<|kn|>"),
            ("Kazakh",           "<|kk|>"),
            ("Khmer",            "<|km|>"),
            ("Korean",           "<|ko|>"),
            ("Latin",            "<|la|>"),
            ("Latvian",          "<|lv|>"),
            ("Lingala",          "<|ln|>"),
            ("Lithuanian",       "<|lt|>"),
            ("Lao",              "<|lo|>"),
            ("Luxembourgish",    "<|lb|>"),
            ("Macedonian",       "<|mk|>"),
            ("Malagasy",         "<|mg|>"),
            ("Malay",            "<|ms|>"),
            ("Malayalam",        "<|ml|>"),
            ("Maltese",          "<|mt|>"),
            ("Maori",            "<|mi|>"),
            ("Marathi",          "<|mr|>"),
            ("Mongolian",        "<|mn|>"),
            ("Burmese",          "<|my|>"),
            ("Nepali",           "<|ne|>"),
            ("Norwegian",        "<|no|>"),
            ("Norwegian Nynorsk","<|nn|>"),
            ("Occitan",          "<|oc|>"),
            ("Pashto",           "<|ps|>"),
            ("Persian",          "<|fa|>"),
            ("Polish",           "<|pl|>"),
            ("Portuguese",       "<|pt|>"),
            ("Punjabi",          "<|pa|>"),
            ("Romanian",         "<|ro|>"),
            ("Russian",          "<|ru|>"),
            ("Sanskrit",         "<|sa|>"),
            ("Serbian",          "<|sr|>"),
            ("Shona",            "<|sn|>"),
            ("Sindhi",           "<|sd|>"),
            ("Sinhala",          "<|si|>"),
            ("Slovak",           "<|sk|>"),
            ("Slovenian",        "<|sl|>"),
            ("Somali",           "<|so|>"),
            ("Spanish",          "<|es|>"),
            ("Albanian",         "<|sq|>"),
            ("Sundanese",        "<|su|>"),
            ("Swahili",          "<|sw|>"),
            ("Swedish",          "<|sv|>"),
            ("Tagalog",          "<|tl|>"),
            ("Tajik",            "<|tg|>"),
            ("Tamil",            "<|ta|>"),
            ("Tatar",            "<|tt|>"),
            ("Telugu",           "<|te|>"),
            ("Thai",             "<|th|>"),
            ("Tibetan",          "<|bo|>"),
            ("Turkmen",          "<|tk|>"),
            ("Turkish",          "<|tr|>"),
            ("Ukrainian",        "<|uk|>"),
            ("Urdu",             "<|ur|>"),
            ("Uzbek",            "<|uz|>"),
            ("Vietnamese",       "<|vi|>"),
            ("Welsh",            "<|cy|>"),
            ("Yiddish",          "<|yi|>"),
            ("Yoruba",           "<|yo|>"),
        ]
        for name, token in _languages:
            self.language_selector.addItem(name, token)
        options_layout.addWidget(self.language_selector)
        
        options_layout.addWidget(QLabel("Task:"))
        self.task_selector = QComboBox()
        self.task_selector.addItem("Transcribe", "transcribe")
        self.task_selector.addItem("Translate to English", "translate")
        options_layout.addWidget(self.task_selector)
        
        audio_group.addLayout(options_layout)
        
        self.transcribe_btn = QPushButton("▶ Transcribe")
        self.transcribe_btn.setObjectName("primaryButton")
        self.transcribe_btn.setMinimumHeight(40)
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self.start_transcription)
        audio_group.addWidget(self.transcribe_btn)
        
        layout.addLayout(audio_group)
        
        # --- Output Section ---
        output_label = QLabel("<b>3. Transcription Result</b>")
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Transcription will appear here...")
        layout.addWidget(self.output_text)
        
        # --- Bottom Buttons ---
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_output)
        button_layout.addWidget(self.copy_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def download_model(self):
        repo_id = self.model_selector.currentText().strip()
        if not repo_id:
            QMessageBox.warning(self, "Input Error", "Please enter a Hugging Face repository ID.")
            return
            
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indeterminate
        
        # Update status text based on locality
        local_path = self.manager.models_dir / repo_id.replace("/", "--")
        if local_path.exists() and (local_path / "openvino_model.xml").exists():
            self.model_status_label.setText(f"Verifying local model {repo_id}...")
        else:
            self.model_status_label.setText(f"Downloading {repo_id} from Hugging Face...")
        
        self.worker = STTWorker("download", self.manager, repo_id=repo_id)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_progress(self, p):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(p)

    def on_download_finished(self, model_path):
        # After download, start loading the model in the background
        self.model_status_label.setText(f"Loading model into memory...")
        self.worker = STTWorker("load", self.manager, model_path=model_path)
        self.worker.finished.connect(self.on_load_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_load_finished(self, success):
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            model_path = self.manager.current_model_path
            self.model_status_label.setText(f"✓ Model loaded: {model_path.name}")
            self.model_status_label.setStyleSheet("color: #00ff00; font-size: 10px;")
            
            # Add to combo box if new
            repo_id = self.model_selector.currentText().strip()
            if self.model_selector.findText(repo_id) == -1:
                self.model_selector.addItem(repo_id)
                
            self.update_transcribe_btn_state()
            # QMessageBox.information(self, "Success", "Model loaded successfully!")
        else:
            self.model_status_label.setText("❌ Failed to load model")
            self.model_status_label.setStyleSheet("color: #ff0000; font-size: 10px;")
            self.update_transcribe_btn_state()

    def browse_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", "", "Media Files (*.mp3 *.wav *.m4a *.mp4);;All Files (*)"
        )
        if file_path:
            self.audio_path_input.setText(file_path)
            self.update_transcribe_btn_state()

    def start_transcription(self):
        audio_path = Path(self.audio_path_input.text())
        if not audio_path.exists():
            QMessageBox.warning(self, "File Error", "The selected audio file does not exist.")
            return
            
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.output_text.clear()
        self.output_text.setPlaceholderText("Transcribing... please wait.")
        
        language_val = self.language_selector.currentData()
        task_val = self.task_selector.currentData()
        
        self.worker = STTWorker(
            "transcribe", 
            self.manager, 
            audio_path=audio_path,
            language=language_val if language_val else None,
            inference_task=task_val
        )
        self.worker.new_text.connect(self.on_new_text)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_new_text(self, text):
        # Move cursor to end and insert
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()

    def on_transcription_finished(self, text):
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.output_text.setPlainText(text)
        self.output_text.setPlaceholderText("Transcription complete.")

    def on_worker_error(self, error_msg):
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"An error occurred: {error_msg}")
        self.model_status_label.setText("❌ Error occurred")

    def set_ui_enabled(self, enabled):
        self.download_btn.setEnabled(enabled)
        self.model_selector.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
        self.copy_btn.setEnabled(enabled)
        self.update_transcribe_btn_state()

    def update_transcribe_btn_state(self):
        """Update the enabled state of the transcribe button."""
        has_pipeline = self.manager.pipeline is not None
        has_file = bool(self.audio_path_input.text().strip())
        is_not_busy = self.download_btn.isEnabled()
        self.transcribe_btn.setEnabled(has_pipeline and has_file and is_not_busy)

    def copy_output(self):
        text = self.output_text.toPlainText()
        if text:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.model_status_label.setText("✓ Copied to clipboard")
        else:
            QMessageBox.information(self, "Info", "Nothing to copy.")
