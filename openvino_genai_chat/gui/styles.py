"""Centralized stylesheet for modern PyQt5 interface."""

from typing import Optional


def get_stylesheet(theme: str = "dark") -> str:
    """
    Get the stylesheet for the application.
    
    Args:
        theme: Theme name ("dark" or "light")
        
    Returns:
        CSS stylesheet string
    """
    if theme == "light":
        return get_light_stylesheet()
    else:
        return get_dark_stylesheet()


def get_dark_stylesheet() -> str:
    """Get dark theme stylesheet."""
    return """
    /* Main Window */
    QMainWindow {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Central Widget */
    QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Toolbars and Specialized Containers */
    QWidget#toolbarWidget, QWidget#inputWidget {
        background-color: #252525;
        border-bottom: 1px solid #3d3d3d;
    }
    
    QWidget#inputWidget {
        border-top: 1px solid #3d3d3d;
        border-bottom: none;
    }
    
    QWidget#sidebarWidget {
        background-color: #1e1e1e;
        border-right: 1px solid #3d3d3d;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #0d7377;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
        font-size: 11px;
    }
    
    QPushButton:hover {
        background-color: #14919b;
    }
    
    QPushButton:pressed {
        background-color: #0a5a62;
    }
    
    QPushButton:disabled {
        background-color: #404040;
        color: #808080;
    }
    
    QPushButton#primaryButton {
        background-color: #0d7377;
    }
    
    QPushButton#primaryButton:hover {
        background-color: #14919b;
    }
    
    QPushButton#dangerButton {
        background-color: #d32f2f;
    }
    
    QPushButton#dangerButton:hover {
        background-color: #e53935;
    }
    
    /* Toggle Button */
    QPushButton#toggleButton {
        background-color: #444444;
        padding: 8px 16px;
    }
    
    QPushButton#toggleButton:checked {
        background-color: #0d7377;
    }
    
    /* Text Input */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        padding: 6px;
        selection-background-color: #0d7377;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #0d7377;
        outline: none;
    }
    
    /* Scrollbars */
    QScrollBar:vertical {
        background-color: #2d2d2d;
        width: 12px;
        border: none;
    }
    
    QScrollBar::handle:vertical {
        background-color: #505050;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #606060;
    }
    
    QScrollBar:horizontal {
        background-color: #2d2d2d;
        height: 12px;
        border: none;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #505050;
        border-radius: 6px;
        min-width: 20px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #606060;
    }
    
    QScrollBar::sub-line, QScrollBar::add-line {
        background: none;
        border: none;
    }
    
    /* Splitter */
    QSplitter::handle {
        background-color: #3d3d3d;
    }
    
    QSplitter::handle:hover {
        background-color: #505050;
    }
    
    /* List Widget */
    QListWidget, QListView {
        background-color: #252525;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        outline: none;
    }
    
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #2d2d2d;
    }
    
    QListWidget::item:selected {
        background-color: #0d7377;
        color: #ffffff;
    }
    
    QListWidget::item:hover {
        background-color: #333333;
    }
    
    /* Combo Box */
    QComboBox {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        padding: 4px 8px;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-top: 5px solid #0d7377;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        margin-top: 2px;
        margin-right: 5px;
        width: 0px;
        height: 0px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #2d2d2d;
        color: #ffffff;
        selection-background-color: #0d7377;
        border: 1px solid #3d3d3d;
    }
    
    /* Slider */
    QSlider::groove:horizontal {
        background-color: #3d3d3d;
        height: 6px;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background-color: #0d7377;
        width: 18px;
        margin: -6px 0px;
        border-radius: 9px;
    }
    
    /* Labels */
    QLabel {
        color: #ffffff;
    }
    
    /* Dialogs */
    QDialog {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Checkboxes */
    QCheckBox {
        color: #ffffff;
        spacing: 5px;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid #3d3d3d;
        background-color: #2d2d2d;
    }
    
    QCheckBox::indicator:checked {
        background-color: #0d7377;
        border: 1px solid #0d7377;
    }
    
    /* GroupBox */
    QGroupBox {
        color: #ffffff;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
    }
    """


def get_light_stylesheet() -> str:
    """Get light theme stylesheet."""
    return """
    /* Main Window */
    QMainWindow {
        background-color: #fefefe;
        color: #222222;
    }
    
    /* Central Widget */
    QWidget {
        background-color: #fefefe;
        color: #222222;
    }
    
    /* Toolbars and Specialized Containers */
    QWidget#toolbarWidget, QWidget#inputWidget {
        background-color: #f5f5f5;
        border-bottom: 1px solid #dddddd;
    }
    
    QWidget#inputWidget {
        border-top: 1px solid #dddddd;
        border-bottom: none;
    }
    
    QWidget#sidebarWidget {
        background-color: #fefefe;
        border-right: 1px solid #dddddd;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #0d7377;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
        font-size: 11px;
    }
    
    QPushButton:hover {
        background-color: #14919b;
    }
    
    QPushButton:pressed {
        background-color: #0a5a62;
    }
    
    QPushButton:disabled {
        background-color: #e0e0e0;
        color: #999999;
    }
    
    /* Toggle Button */
    QPushButton#toggleButton {
        background-color: #dddddd;
        color: #444444;
        padding: 8px 16px;
    }
    
    QPushButton#toggleButton:checked {
        background-color: #0d7377;
        color: #ffffff;
    }
    
    /* Text Input */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        color: #222222;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 6px;
        selection-background-color: #0d7377;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #0d7377;
    }
    
    /* Scrollbars */
    QScrollBar:vertical {
        background-color: #f5f5f5;
        width: 12px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #cccccc;
        border-radius: 6px;
    }
    
    /* Splitter */
    QSplitter::handle {
        background-color: #dddddd;
    }
    
    /* List Widget */
    QListWidget, QListView {
        background-color: #ffffff;
        color: #222222;
        border: 1px solid #dddddd;
        border-radius: 4px;
    }
    
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #f0f0f0;
    }
    
    QListWidget::item:selected {
        background-color: #0d7377;
        color: #ffffff;
    }
    
    QListWidget::item:hover {
        background-color: #f8f8f8;
    }
    
    /* Combo Box */
    QComboBox {
        background-color: #ffffff;
        color: #222222;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 4px 8px;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    QComboBox::down-arrow {
        image: none;
        border-top: 5px solid #0d7377;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        margin-top: 2px;
        margin-right: 5px;
        width: 0px;
        height: 0px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #222222;
        selection-background-color: #0d7377;
        border: 1px solid #cccccc;
    }
    
    /* Labels */
    QLabel {
        color: #222222;
    }
    
    /* Dialogs */
    QDialog {
        background-color: #fefefe;
        color: #222222;
    }
    
    /* GroupBox */
    QGroupBox {
        color: #222222;
        border: 1px solid #dddddd;
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
    }
    """

