"""Application settings dialog."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SettingsDialog(QDialog):
    """Dialog for application-wide settings."""
    
    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(str, object)  # key, value
    
    def __init__(self, current_theme: str = "dark", parent=None):
        """
        Initialize settings dialog.
        
        Args:
            current_theme: Current theme (dark or light)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        self.current_theme = current_theme
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Theme selection group
        theme_group = QGroupBox("Appearance")
        theme_layout = QHBoxLayout()
        
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Other settings can be added here
        layout.addStretch()
        
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
        self.theme_combo.setCurrentText(self.current_theme)
    
    def apply_settings(self) -> None:
        """Apply the configured settings."""
        theme = self.theme_combo.currentText()
        
        if theme != self.current_theme:
            logger.info(f"Theme changed to: {theme}")
            self.settings_changed.emit("theme", theme)
        
        self.accept()
