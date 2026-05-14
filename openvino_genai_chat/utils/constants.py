"""Application constants and configuration values."""

import os
from pathlib import Path
from enum import Enum

# Application directories
APP_DIR = Path.home() / ".openvino_genai_chat"
CONVERSATIONS_DIR = APP_DIR / "conversations"
TEMPLATES_DIR = APP_DIR / "templates"
CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE = APP_DIR / "app.log"

# Ensure directories exist
for dir_path in [APP_DIR, CONVERSATIONS_DIR, TEMPLATES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class Device(Enum):
    """Inference device options."""
    CPU = "CPU"
    GPU = "GPU"


# Default configuration
DEFAULT_CONFIG = {
    "model_path": str(APP_DIR / "models" / "OpenVINO" / "Phi-3.5-mini-instruct-int4-ov"),
    "device": Device.CPU.value,
    "max_new_tokens": 4096,
    "theme": "dark",
    "auto_save_interval": 5,  # seconds
    "use_thinking": False,  # /no_think by default, set True for /think
    "cancel_wait_ms": 5000,  # ms to wait for generation worker before force-terminating
}

# Model inference limits
MIN_TOKENS = 256
MAX_TOKENS = 16384
DEFAULT_TOKENS = 4096

# UI Settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 300
CHAT_BUBBLE_MAX_WIDTH = 2000

# Chat display settings
STREAMING_UPDATE_INTERVAL = 50  # milliseconds between UI updates during streaming
MESSAGE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# Conversation file settings
CONVERSATION_FILE_EXTENSION = ".json"
MAX_CONVERSATION_TITLE_LENGTH = 100

# Template settings
BUILTIN_TEMPLATES = []
CUSTOM_TEMPLATES_FILE = TEMPLATES_DIR / "custom_templates.json"

# Initial setup
INITIAL_MODEL_ID = "OpenVINO/Phi-3.5-mini-instruct-int4-ov"
