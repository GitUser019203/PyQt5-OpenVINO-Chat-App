"""Application settings management and persistence."""

import json
from pathlib import Path
from typing import Any, Dict
from .constants import CONFIG_FILE, DEFAULT_CONFIG, Device
from .logger import setup_logger

logger = setup_logger(__name__)


class SettingsManager:
    """
    Manages application settings persistence.
    Handles reading/writing settings to config file with default values.
    """
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        """
        Initialize settings manager.
        
        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file or create defaults.
        
        Returns:
            Dictionary of settings
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Settings loaded from {self.config_file}")
                return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
        
        # Return defaults if file doesn't exist or error occurred
        return DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
    
    def save(self) -> None:
        """Save current settings to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            logger.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get_model_path(self) -> Path:
        """Get model path as Path object."""
        return Path(self.get("model_path"))
    
    def get_device(self) -> Device:
        """Get device as Device enum."""
        device_str = self.get("device", Device.CPU.value)
        return Device(device_str)
    
    def get_max_tokens(self) -> int:
        """Get max tokens setting."""
        return self.get("max_new_tokens", 4096)
    
    def get_use_thinking(self) -> bool:
        """Get whether extended thinking (/think) is enabled."""
        return self.get("use_thinking", False)
    
    def set_use_thinking(self, enabled: bool) -> None:
        """Set extended thinking mode."""
        self.set("use_thinking", enabled)
        self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings = DEFAULT_CONFIG.copy()
        self.save()
