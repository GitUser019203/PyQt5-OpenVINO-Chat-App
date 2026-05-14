"""Model configuration dialog."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSlider, QComboBox, QFileDialog, QSpinBox, QGroupBox, QMessageBox,
    QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from pathlib import Path
from ..utils.constants import Device, MIN_TOKENS, MAX_TOKENS, DEFAULT_TOKENS
from ..utils.logger import setup_logger
from ..models.model_manager import ModelManager

logger = setup_logger(__name__)


class DownloadWorker(QThread):
    """Worker thread for downloading GenAI models."""
    
    finished = pyqtSignal(Path)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, repo_id: str, target_dir: Path):
        super().__init__()
        self.repo_id = repo_id
        self.target_dir = target_dir
        
    def run(self):
        try:
            manager = ModelManager.get_instance()
            def progress_cb(p):
                self.progress.emit(p)
                
            model_path = manager.download_model(
                self.repo_id, 
                self.target_dir, 
                progress_callback=progress_cb
            )
            self.finished.emit(model_path)
        except Exception as e:
            logger.error(f"Download worker error: {e}")
            self.error.emit(str(e))


class ConfigDialog(QDialog):
    """Dialog for configuring model inference settings."""
    
    # Signal emitted when settings are applied
    settings_applied = pyqtSignal(str, str, int, bool, int)  # model_path, device, max_tokens, use_thinking, cancel_wait_ms
    
    def __init__(self, 
                 current_model_path: str,
                 current_device: str,
                 current_max_tokens: int,
                 current_use_thinking: bool,
                 current_cancel_wait_ms: int = 5000,
                 parent=None):
        """
        Initialize configuration dialog.
        
        Args:
            current_model_path: Current model path
            current_device: Current device (CPU or GPU)
            current_max_tokens: Current max tokens setting
            current_use_thinking: Current thinking mode state
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setMinimumWidth(500)
        
        self.current_model_path = current_model_path
        self.current_device = current_device
        self.current_max_tokens = current_max_tokens
        self.current_use_thinking = current_use_thinking
        self.current_cancel_wait_ms = current_cancel_wait_ms
        self.worker = None
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Model path group
        model_group = QGroupBox("Model Configuration")
        model_layout = QHBoxLayout()
        
        QLabel("Model Path:")
        self.model_path_input = QLineEdit()
        self.model_path_input.setPlaceholderText("Path to OpenVINO model directory")
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_model_path)
        
        model_layout.addWidget(QLabel("Model Path:"))
        model_layout.addWidget(self.model_path_input)
        model_layout.addWidget(browse_btn)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Download model group
        download_group = QGroupBox("Download New Model")
        download_v_layout = QVBoxLayout()
        
        download_h_layout = QHBoxLayout()
        download_h_layout.addWidget(QLabel("HF Repo ID:"))
        self.repo_id_input = QLineEdit()
        self.repo_id_input.setPlaceholderText("e.g., OpenVINO/Phi-3.5-mini-instruct-int4-ov")
        download_h_layout.addWidget(self.repo_id_input)
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        download_h_layout.addWidget(self.download_btn)
        download_v_layout.addLayout(download_h_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        download_v_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Models will be downloaded to standard local directory.")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px;")
        download_v_layout.addWidget(self.status_label)
        
        download_group.setLayout(download_v_layout)
        layout.addWidget(download_group)
        
        # Device selection group
        device_group = QGroupBox("Device Selection")
        device_layout = QHBoxLayout()
        
        device_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems([Device.CPU.value, Device.GPU.value])
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Token limits group
        tokens_group = QGroupBox("Generation Parameters")
        tokens_layout = QVBoxLayout()
        
        # Max tokens
        tokens_h_layout = QHBoxLayout()
        tokens_h_layout.addWidget(QLabel("Max Tokens:"))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setMinimum(MIN_TOKENS)
        self.max_tokens_spin.setMaximum(MAX_TOKENS)
        self.max_tokens_spin.setValue(DEFAULT_TOKENS)
        self.max_tokens_spin.setSingleStep(256)
        tokens_h_layout.addWidget(self.max_tokens_spin)
        tokens_h_layout.addStretch()
        tokens_layout.addLayout(tokens_h_layout)
        
        # Token slider
        self.tokens_slider = QSlider(Qt.Horizontal)
        self.tokens_slider.setMinimum(MIN_TOKENS)
        self.tokens_slider.setMaximum(MAX_TOKENS)
        self.tokens_slider.setValue(DEFAULT_TOKENS)
        self.tokens_slider.setSingleStep(256)
        self.tokens_slider.setTickInterval(2048)
        self.tokens_slider.setTickPosition(QSlider.TicksBelow)
        self.tokens_slider.sliderMoved.connect(self._update_tokens_from_slider)
        tokens_layout.addWidget(self.tokens_slider)
        
        # Cancel wait time
        cancel_h_layout = QHBoxLayout()
        cancel_h_layout.addWidget(QLabel("Cancel Wait (ms):"))
        self.cancel_wait_spin = QSpinBox()
        self.cancel_wait_spin.setMinimum(500)
        self.cancel_wait_spin.setMaximum(1000000)
        self.cancel_wait_spin.setSingleStep(500)
        self.cancel_wait_spin.setValue(5000)
        self.cancel_wait_spin.setToolTip(
            "How long to wait for the generation worker to stop gracefully\n"
            "before forcefully terminating it. Increase if you see\n"
            "'terminating forcefully' warnings in the logs."
        )
        cancel_h_layout.addWidget(self.cancel_wait_spin)
        cancel_h_layout.addStretch()
        tokens_layout.addLayout(cancel_h_layout)
        
        tokens_group.setLayout(tokens_layout)
        layout.addWidget(tokens_group)
        
        # Thinking mode group
        thinking_group = QGroupBox("Inference Mode")
        thinking_layout = QHBoxLayout()
        
        thinking_layout.addWidget(QLabel("Extended Thinking:"))
        self.thinking_combo = QComboBox()
        self.thinking_combo.addItems(["/no_think (faster)", "/think (slower, more reasoning)"])
        thinking_layout.addWidget(self.thinking_combo)
        thinking_layout.addStretch()
        thinking_group.setLayout(thinking_layout)
        layout.addWidget(thinking_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self) -> None:
        """Load current settings into UI."""
        self.model_path_input.setText(self.current_model_path)
        self.device_combo.setCurrentText(self.current_device)
        self.max_tokens_spin.setValue(self.current_max_tokens)
        self.tokens_slider.setValue(self.current_max_tokens)
        self.cancel_wait_spin.setValue(self.current_cancel_wait_ms)
        
        if self.current_use_thinking:
            self.thinking_combo.setCurrentIndex(1)
        else:
            self.thinking_combo.setCurrentIndex(0)
    
    def browse_model_path(self) -> None:
        """Open file dialog to select model path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select OpenVINO Model Directory",
            self.current_model_path or str(Path.home()),
        )
        
        if path:
            self.model_path_input.setText(path)
    
    def _update_tokens_from_slider(self, value: int) -> None:
        """Update spin box when slider changes."""
        self.max_tokens_spin.blockSignals(True)
        self.max_tokens_spin.setValue(value)
        self.max_tokens_spin.blockSignals(False)
    
    def apply_settings(self) -> None:
        """Apply the configured settings."""
        model_path = self.model_path_input.text().strip()
        device = self.device_combo.currentText()
        max_tokens = self.max_tokens_spin.value()
        use_thinking = self.thinking_combo.currentIndex() == 1
        cancel_wait_ms = self.cancel_wait_spin.value()
        
        # Validate model path
        if not model_path:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please specify a model path.",
            )
            return
        
        if not Path(model_path).exists():
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Model path does not exist: {model_path}",
            )
            return
        
        logger.info(f"Applying config: model={model_path}, device={device}, tokens={max_tokens}, cancel_wait_ms={cancel_wait_ms}")
        self.settings_applied.emit(model_path, device, max_tokens, use_thinking, cancel_wait_ms)
        self.accept()

    def start_download(self):
        """Start the model download process."""
        repo_id = self.repo_id_input.text().strip()
        if not repo_id:
            QMessageBox.warning(self, "Input Error", "Please enter a Hugging Face repository ID.")
            return

        # Determine target directory (sibling of current model path or app dir)
        if self.current_model_path:
            target_dir = Path(self.current_model_path).parent
        else:
            target_dir = Path.home() / ".openvino_genai_chat" / "models"

        self.repo_id_input.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Downloading {repo_id}...")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px;")

        self.worker = DownloadWorker(repo_id, target_dir)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_progress(self, value):
        """Update progress bar."""
        self.progress_bar.setValue(value)

    def on_finished(self, model_path: Path):
        """Handle download completion."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✓ Download complete: {model_path}")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 10px;")
        self.model_path_input.setText(str(model_path))
        
        # Apply settings which will trigger restart prompt in MainWindow
        self.apply_settings()

    def on_error(self, message):
        """Handle download error."""
        self.repo_id_input.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ Error: {message}")
        self.status_label.setStyleSheet("color: #ff0000; font-size: 10px;")
        QMessageBox.critical(self, "Download Error", f"Failed to download model: {message}")
