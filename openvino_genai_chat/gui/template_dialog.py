"""Template selection and input dialog."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QWidget, QScrollArea
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Optional, Dict
from ..templates.template_manager import Template, TemplateField, TemplateManager, CustomTemplate
from .template_editor import TemplateEditorDialog
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TemplateDialog(QDialog):
    """Dialog for selecting and configuring templates."""
    
    # Signal emitted when template is applied
    template_applied = pyqtSignal(str)  # generated_prompt
    
    def __init__(self, template_manager: TemplateManager, parent=None):
        """
        Initialize template dialog.
        
        Args:
            template_manager: Template manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Chat Templates")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.template_manager = template_manager
        self.current_template: Optional[Template] = None
        self.template_inputs: Dict[str, QWidget] = {}
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Template selection
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Select Template:"))
        
        self.template_combo = QComboBox()
        
        for template_info in self.template_manager.list_templates():
            self.template_combo.addItem(
                template_info["name"],
                template_info["description"]
            )
        
        select_layout.addWidget(self.template_combo)
        
        # Management buttons
        self.new_btn = QPushButton("+ New")
        self.new_btn.setToolTip("Create new template")
        self.new_btn.clicked.connect(self.create_template)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setToolTip("Edit selected template")
        self.edit_btn.clicked.connect(self.edit_template)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.setToolTip("Delete selected template")
        self.delete_btn.clicked.connect(self.delete_template)
        
        select_layout.addWidget(self.new_btn)
        select_layout.addWidget(self.edit_btn)
        select_layout.addWidget(self.delete_btn)
        
        layout.addLayout(select_layout)
        
        # Template description
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self.description_label)
        
        # Scrollable input fields area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout()
        self.fields_layout.setSpacing(12)
        self.fields_container.setLayout(self.fields_layout)
        
        scroll.setWidget(self.fields_container)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply Template")
        apply_btn.clicked.connect(self.apply_template)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals and load first template
        if self.template_combo.count() > 0:
            self.on_template_changed(0)
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
    
    def on_template_changed(self, index: int) -> None:
        """Handle template selection change."""
        template_name = self.template_combo.itemText(index)
        self.current_template = self.template_manager.get_template(template_name)
        
        if not self.current_template:
            return
        
        # Update description
        self.description_label.setText(self.current_template.description)
        
        # Enable/disable edit/delete based on whether it's custom
        is_custom = isinstance(self.current_template, CustomTemplate)
        self.edit_btn.setEnabled(is_custom)
        self.delete_btn.setEnabled(is_custom)
        
        # Clear previous fields
        self._clear_layout(self.fields_layout)
        
        self.template_inputs = {}
        
        # Create input fields
        for field in self.current_template.fields:
            field_group_layout = QVBoxLayout()
            
            # Label
            label_text = field.label
            if field.required:
                label_text += " *"
            label = QLabel(label_text)
            field_group_layout.addWidget(label)
            
            # Input widget
            if field.multiline:
                input_widget = QTextEdit()
                input_widget.setPlaceholderText(field.placeholder)
                input_widget.setMinimumHeight(100)
            else:
                input_widget = QLineEdit()
                input_widget.setPlaceholderText(field.placeholder)
            
            field_group_layout.addWidget(input_widget)
            self.fields_layout.addLayout(field_group_layout)
            
            self.template_inputs[field.name] = input_widget
        
        # Add stretch at the end
        self.fields_layout.addStretch()

    def _clear_layout(self, layout) -> None:
        """
        Recursively clear all items from a layout and delete widgets.
        
        Args:
            layout: The layout to clear
        """
        if layout is None:
            return
            
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def refresh_templates(self, select_name: Optional[str] = None) -> None:
        """Refresh the template list and optionally select one by name."""
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        
        for template_info in self.template_manager.list_templates():
            self.template_combo.addItem(
                template_info["name"],
                template_info["description"]
            )
        
        if select_name:
            index = self.template_combo.findText(select_name)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)
        
        self.template_combo.blockSignals(False)
        self.on_template_changed(self.template_combo.currentIndex())

    def create_template(self) -> None:
        """Open editor to create a new template."""
        dialog = TemplateEditorDialog(parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.template_manager.save_custom_template(
                name=data["name"],
                description=data["description"],
                fields=data["fields"],
                prompt_template=data["prompt_template"]
            )
            self.refresh_templates(data["name"])

    def edit_template(self) -> None:
        """Open editor to edit the current template."""
        if not isinstance(self.current_template, CustomTemplate):
            return
            
        dialog = TemplateEditorDialog(template=self.current_template, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.template_manager.save_custom_template(
                name=data["name"],
                description=data["description"],
                fields=data["fields"],
                prompt_template=data["prompt_template"]
            )
            self.refresh_templates(data["name"])

    def delete_template(self) -> None:
        """Delete the current template."""
        if not isinstance(self.current_template, CustomTemplate):
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{self.current_template.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.template_manager.delete_custom_template(self.current_template.name)
            self.refresh_templates()
    
    def apply_template(self) -> None:
        """Apply the selected template and emit the generated prompt."""
        if not self.current_template:
            QMessageBox.warning(self, "Error", "No template selected.")
            return
        
        # Collect inputs
        inputs = {}
        for field_name, input_widget in self.template_inputs.items():
            if isinstance(input_widget, QTextEdit):
                inputs[field_name] = input_widget.toPlainText()
            else:
                inputs[field_name] = input_widget.text()
        
        # Validate inputs
        is_valid, error_msg = self.current_template.validate_inputs(inputs)
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Generate prompt
        try:
            prompt = self.current_template.generate_prompt(inputs)
            logger.info(f"Applied template: {self.current_template.name}")
            self.template_applied.emit(prompt)
            self.accept()
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate prompt: {str(e)}"
            )
