"""Dialog for creating and editing custom templates."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QWidget, QScrollArea,
    QCheckBox, QFrame
)
from PyQt5.QtCore import Qt
from typing import List, Optional
from ..templates.template_manager import Template, TemplateField, CustomTemplate


class FieldEditorWidget(QFrame):
    """Widget for editing a single template field."""
    
    def __init__(self, field: Optional[TemplateField] = None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("FieldEditorWidget { background-color: rgba(255, 255, 255, 0.05); border-radius: 4px; }")
        
        layout = QVBoxLayout()
        
        # Row 1: Label and Name
        row1 = QHBoxLayout()
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Field Label (e.g., Job Posting)")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Internal Name (e.g., job_posting)")
        
        row1.addWidget(QLabel("Label:"))
        row1.addWidget(self.label_input)
        row1.addWidget(QLabel("Name:"))
        row1.addWidget(self.name_input)
        layout.addLayout(row1)
        
        # Row 2: Placeholder and Options
        row2 = QHBoxLayout()
        self.placeholder_input = QLineEdit()
        self.placeholder_input.setPlaceholderText("Placeholder text...")
        
        self.required_check = QCheckBox("Required")
        self.required_check.setChecked(True)
        self.multiline_check = QCheckBox("Multiline")
        
        row2.addWidget(QLabel("Placeholder:"))
        row2.addWidget(self.placeholder_input)
        row2.addWidget(self.required_check)
        row2.addWidget(self.multiline_check)
        layout.addLayout(row2)
        
        # Delete button
        self.delete_btn = QPushButton("Remove Field")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.setMaximumWidth(100)
        layout.addWidget(self.delete_btn, 0, Qt.AlignRight)
        
        self.setLayout(layout)
        
        if field:
            self.label_input.setText(field.label)
            self.name_input.setText(field.name)
            self.placeholder_input.setText(field.placeholder)
            self.required_check.setChecked(field.required)
            self.multiline_check.setChecked(field.multiline)

    def get_field(self) -> TemplateField:
        """Get the TemplateField representation of current inputs."""
        return TemplateField(
            name=self.name_input.text().strip(),
            label=self.label_input.text().strip(),
            placeholder=self.placeholder_input.text().strip(),
            required=self.required_check.isChecked(),
            multiline=self.multiline_check.isChecked()
        )


class TemplateEditorDialog(QDialog):
    """Dialog for creating/editing a template."""
    
    def __init__(self, template: Optional[CustomTemplate] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Template Editor")
        self.setMinimumSize(700, 600)
        
        self.template = template
        self.field_widgets: List[FieldEditorWidget] = []
        
        self.setup_ui()
        if template:
            self.load_template(template)
            
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Basic Info
        info_layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Template Name (e.g., code_reviewer)")
        if self.template:
            self.name_input.setReadOnly(True)  # Don't allow renaming key
            self.name_input.setStyleSheet("color: #888888;")
            
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Short description...")
        
        info_layout.addWidget(QLabel("<b>Name (Internal ID):</b>"))
        info_layout.addWidget(self.name_input)
        info_layout.addWidget(QLabel("<b>Description:</b>"))
        info_layout.addWidget(self.desc_input)
        main_layout.addLayout(info_layout)
        
        # Fields Section
        fields_header = QHBoxLayout()
        fields_header.addWidget(QLabel("<b>Input Fields:</b>"))
        add_field_btn = QPushButton("+ Add Field")
        add_field_btn.clicked.connect(lambda: self.add_field_widget())
        fields_header.addWidget(add_field_btn)
        main_layout.addLayout(fields_header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.fields_container)
        main_layout.addWidget(self.scroll, 2)
        
        # Prompt Template Section
        main_layout.addWidget(QLabel("<b>Prompt Template:</b>"))
        help_label = QLabel("Use {field_name} to insert field values.")
        help_label.setStyleSheet("color: #888888; font-size: 10px;")
        main_layout.addWidget(help_label)
        
        self.prompt_template_input = QTextEdit()
        self.prompt_template_input.setPlaceholderText("E.g. Please review the following code:\n\n{code}\n\nFocus on: {focus}")
        main_layout.addWidget(self.prompt_template_input, 1)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Template")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_template)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)

    def add_field_widget(self, field: Optional[TemplateField] = None) -> None:
        widget = FieldEditorWidget(field)
        widget.delete_btn.clicked.connect(lambda: self.remove_field_widget(widget))
        self.field_widgets.append(widget)
        self.fields_layout.addWidget(widget)

    def remove_field_widget(self, widget: FieldEditorWidget) -> None:
        self.field_widgets.remove(widget)
        widget.deleteLater()

    def load_template(self, template: CustomTemplate) -> None:
        self.name_input.setText(template.name)
        self.desc_input.setText(template.description)
        self.prompt_template_input.setPlainText(template.prompt_template)
        for field in template.fields:
            self.add_field_widget(field)

    def save_template(self) -> None:
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        prompt = self.prompt_template_input.toPlainText().strip()
        
        if not name or not desc or not prompt:
            QMessageBox.warning(self, "Invalid Input", "Name, Description, and Prompt Template are required.")
            return
            
        fields = []
        for w in self.field_widgets:
            f = w.get_field()
            if not f.name or not f.label:
                QMessageBox.warning(self, "Invalid Field", "Every field must have a label and name.")
                return
            fields.append(f)
            
        if not fields:
             QMessageBox.warning(self, "Invalid Template", "A template must have at least one field.")
             return

        self.result_data = {
            "name": name,
            "description": desc,
            "fields": fields,
            "prompt_template": prompt
        }
        self.accept()

    def get_data(self) -> dict:
        return self.result_data
