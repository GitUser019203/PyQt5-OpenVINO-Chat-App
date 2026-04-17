"""Template system for predefined and custom conversation prompts."""

import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from ..utils.logger import setup_logger
from ..utils.constants import TEMPLATES_DIR

logger = setup_logger(__name__)


@dataclass
class TemplateField:
    """Represents an input field in a template."""
    name: str
    label: str
    placeholder: str
    required: bool = True
    multiline: bool = False


class Template(ABC):
    """Abstract base class for conversation templates."""
    
    def __init__(
        self,
        name: str,
        description: str,
        fields: List[TemplateField],
    ):
        """
        Initialize template.
        
        Args:
            name: Template identifier
            description: Human-readable description
            fields: List of input fields
        """
        self.name = name
        self.description = description
        self.fields = fields
    
    @abstractmethod
    def generate_prompt(self, inputs: Dict[str, str]) -> str:
        """
        Generate the model prompt from user inputs.
        
        Args:
            inputs: Dictionary of field names to user input values
            
        Returns:
            Generated prompt for the model
        """
        pass
    
    def validate_inputs(self, inputs: Dict[str, str]) -> tuple[bool, str]:
        """
        Validate user inputs against template fields.
        
        Args:
            inputs: Dictionary of field names to values
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        for field in self.fields:
            if field.required and field.name not in inputs:
                return False, f"Missing required field: {field.label}"
            
            if field.name in inputs and not inputs[field.name].strip():
                if field.required:
                    return False, f"Field cannot be empty: {field.label}"
        
        return True, ""


class TemplateManager:
    """
    Manages built-in and custom templates.
    Loads templates from various sources and coordinates their usage.
    """
    
    def __init__(self, templates_dir: Path = TEMPLATES_DIR):
        """
        Initialize template manager.
        
        Args:
            templates_dir: Directory for storing custom templates
        """
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_templates_file = self.templates_dir / "custom_templates.json"
        self.templates: Dict[str, Template] = {}
        
        self._load_builtin_templates()
        self._load_custom_templates()
        logger.info(f"TemplateManager initialized with {len(self.templates)} templates")
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        # Built-in templates have been removed.
        pass
    
    def _load_custom_templates(self) -> None:
        """Load custom templates from file."""
        if not self.custom_templates_file.exists():
            return
        
        try:
            with open(self.custom_templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for template_data in data.get("templates", []):
                try:
                    template = self._deserialize_custom_template(template_data)
                    self.templates[template.name] = template
                    logger.info(f"Loaded custom template: {template.name}")
                except Exception as e:
                    logger.error(f"Error loading custom template: {e}")
        
        except Exception as e:
            logger.error(f"Error loading custom templates file: {e}")
    
    def _deserialize_custom_template(
        self,
        data: Dict[str, Any],
    ) -> 'CustomTemplate':
        """Deserialize a custom template from JSON data."""
        fields = [
            TemplateField(
                name=f["name"],
                label=f["label"],
                placeholder=f.get("placeholder", ""),
                required=f.get("required", True),
                multiline=f.get("multiline", False),
            )
            for f in data.get("fields", [])
        ]
        
        return CustomTemplate(
            name=data["name"],
            description=data["description"],
            fields=fields,
            prompt_template=data["prompt_template"],
        )
    
    def get_template(self, name: str) -> Optional[Template]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template instance or None if not found
        """
        return self.templates.get(name)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.
        
        Returns:
            List of template information dictionaries
        """
        return [
            {
                "name": t.name,
                "description": t.description,
                "field_count": len(t.fields),
            }
            for t in self.templates.values()
        ]
    
    def save_custom_template(
        self,
        name: str,
        description: str,
        fields: List[TemplateField],
        prompt_template: str,
    ) -> None:
        """
        Save a custom template.
        
        Args:
            name: Template name
            description: Template description
            fields: List of input fields
            prompt_template: Template prompt with {field_name} placeholders
        """
        template = CustomTemplate(
            name=name,
            description=description,
            fields=fields,
            prompt_template=prompt_template,
        )
        
        self.templates[name] = template
        self._save_custom_templates()
        logger.info(f"Saved custom template: {name}")
    
    def delete_custom_template(self, name: str) -> None:
        """
        Delete a custom template.
        
        Args:
            name: Template name
        """
        if name in self.templates:
            del self.templates[name]
            self._save_custom_templates()
            logger.info(f"Deleted custom template: {name}")
    
    def _save_custom_templates(self) -> None:
        """Save all custom templates to file."""
        custom_templates = [
            t for t in self.templates.values()
            if isinstance(t, CustomTemplate)
        ]
        
        data = {
            "templates": [
                {
                    "name": t.name,
                    "description": t.description,
                    "fields": [
                        {
                            "name": f.name,
                            "label": f.label,
                            "placeholder": f.placeholder,
                            "required": f.required,
                            "multiline": f.multiline,
                        }
                        for f in t.fields
                    ],
                    "prompt_template": t.prompt_template,
                }
                for t in custom_templates
            ]
        }
        
        try:
            with open(self.custom_templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving custom templates: {e}")


class CustomTemplate(Template):
    """Custom user-defined template."""
    
    def __init__(
        self,
        name: str,
        description: str,
        fields: List[TemplateField],
        prompt_template: str,
    ):
        """
        Initialize custom template.
        
        Args:
            name: Template name
            description: Template description
            fields: List of input fields
            prompt_template: Template string with {field_name} placeholders
        """
        super().__init__(name, description, fields)
        self.prompt_template = prompt_template
    
    def generate_prompt(self, inputs: Dict[str, str]) -> str:
        """Generate prompt by substituting field values."""
        return self.prompt_template.format(**inputs)
