# OpenVINO GenAI Chat Application

A professional PyQt5-based chat interface for local OpenVINO model inference with real-time streaming, conversation persistence, and template support.

## Features

- **Real-time Streaming**: Watch model responses appear character-by-character as they're generated
- **Speech-to-Text (STT)**:
  - Transcribe audio/video files (`.mp3`, `.m4a`, `.mp4`, `.wav`) using OpenVINO Whisper models
  - Real-time transcription streaming (watch words appear as they are processed)
  - Automatic model downloading and verification from Hugging Face
- **Conversation Persistence**: Automatically save all conversations to disk and revisit them anytime
- **Template System**: Support for user-defined custom templates to streamline repetitive prompts
- **Model Configuration**: 
  - Easy-to-use dialog for model path, device selection (CPU/GPU), and token limits
  - Download new OpenVINO GenAI models directly from Hugging Face
  - Automatic application shutdown to load newly downloaded models
- **Extended Thinking Mode**: Toggle `/think` mode for slower but more reasoning-intensive responses
- **Markdown Support**: Full markdown rendering for both prompts and responses
- **Copy to Clipboard**: Easily copy assistant responses
- **Modern Dark/Light Theme**: Professional, responsive UI with theme support

## Why Local PyQt5? (Security & Privacy)

While web-based alternatives like Streamlit or OpenWebUI are popular, this native desktop application offers several critical cybersecurity advantages:

- **Zero Network Exposure**: Unlike web-based interfaces that open local ports (`localhost:8501`, etc.), this application has no listening network-bound ports. Since it is a self-contained process, it is immune to unauthorized local network access or Cross-Site Request Forgery (CSRF).
- **Reduced Attack Surface**: By avoiding browser engines, we eliminate entire categories of common web vulnerabilities such as Cross-Site Scripting (XSS), insecure cookie management, and data interception via malicious browser extensions.
- **Process Isolation**: The OpenVINO inference engine runs within the application's own memory space. There is no need for a separate Model Server (like OpenVINO Model Server) which would require an open gRPC/REST API port.
- **Data Sovereignty**: Your conversations and settings never leave your machine. The app does not rely on external database servers, cloud backends, or third-party CDNs for its runtime operations.

## Youtube Video
Demo video link : ([https://www.youtube.com/watch?v=ldvx83SdIkY](https://www.youtube.com/watch?v=ldvx83SdIkY))

## Getting Started

On your first launch, the application will automatically download the **Phi-3.5-mini-instruct-int4-ov** model from Hugging Face (~2GB) if no other model is configured. This ensures a seamless "out-of-the-box" experience. Please ensure you have an active internet connection for this initial setup.

## Requirements

- Python 3.8 or higher
- PyQt5 5.15.0 or higher
- OpenVINO GenAI 2024.5.0 or higher
- **FFmpeg**: Required for transcribing non-WAV formats (`.mp3`, `.m4a`, `.mp4`)
- An OpenVINO model (e.g., Phi-3.5-mini-instruct-int4-ov)

## Installation

### From PyPI (when available)

```bash
pip install openvino-genai-chat
openvino-chat
```

### From Wheel File

```bash
pip install dist/openvino_genai_chat-0.1.0-py3-none-any.whl
openvino-chat
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pyqt5-openvino-chat-app.git
cd pyqt5-openvino-chat-app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python -m openvino_genai_chat
```

Or install as a package and use the entry point:
```bash
pip install -e .
openvino-chat
```

### Install FFmpeg (Windows)
For Speech-to-Text to support compressed formats, install FFmpeg using winget:
```powershell
winget install "FFmpeg (Essentials Build)"
```

## Building a Wheel

To build a .whl distribution file:

```bash
pip install build
python -m build
```

The built wheel will be in the `dist/` directory:
```bash
pipx install dist/openvino_genai_chat-0.1.0-py3-none-any.whl
```

## Usage

1. **Configure the Model**:
   - Click "⚙ Config" button
   - Select your OpenVINO model directory
   - Choose CPU or GPU device
   - Set token generation limits
   - Toggle extended thinking mode if desired

2. **Create a New Conversation**:
   - Click "+ New Chat" in the sidebar
   - Or press Ctrl+N

3. **Send Messages**:
   - Type your message in the input area
   - Press Enter to send, or Shift+Enter for new line
   - Watch the response stream in real-time

4. **Use Templates**:
   - Click "📋 Templates" to open template dialog
   - Create or select a custom template
   - Fill in the required fields
   - Click "Apply Template" to populate the chat input

5. **Manage Conversations**:
   - Click on any conversation in the sidebar to load it
   - Right-click to rename or delete
   - Search conversations using the search box

6. **Speech-to-Text**:
   - Click "🎙 STT" in the main toolbar
   - Select an STT model (e.g., `OpenVINO/whisper-base-int8-ov`)
   - Click "Download / Load" to prepare the model
   - Browse for an audio or video file
   - Click "▶ Transcribe" to start processing
   - Watch text appear in real-time

7. **Copy Responses**:
   - Click "📋 Copy Last Response" to copy assistant's message

## Architecture

The application follows a modular, extensible architecture:

```
openvino_genai_chat/
├── gui/                    # PyQt5 user interface
│   ├── main_window.py      # Main application window
│   ├── chat_widget.py      # Chat display with markdown support
│   ├── sidebar.py          # Conversation management sidebar
│   ├── config_dialog.py    # Model configuration
│   ├── template_dialog.py  # Template selection
│   ├── settings_dialog.py  # Application settings
│   └── styles.py           # Centralized styling
├── models/                 # Model integration
│   ├── openvino_wrapper.py # OpenVINO pipeline wrapper
│   └── chat_manager.py     # Conversation state management
├── storage/                # Persistence layer
│   ├── base.py            # Abstract storage interface
│   └── json_backend.py    # JSON file storage
├── templates/              # Template system
│   ├── template_manager.py # Template management
│   └── builtin_templates.py # Built-in templates
└── utils/                  # Utilities
    ├── constants.py        # Application constants
    ├── logger.py           # Logging setup
    └── settings.py         # Settings management
```

### Storage Layer

The storage layer uses an abstract interface that enables future migration to SQLite or other backends without changing application code:

- **Abstract Interface**: `StorageBackend` in `storage/base.py`
- **Current Implementation**: JSON file-based in `storage/json_backend.py`
- **Future**: Easy to implement SQLite or cloud storage backends

### Template System

The extensible template system allows users to create structured prompts:

- **Custom Templates**: User-created templates saved to `~/.openvino_genai_chat/templates/`
- **Field Validation**: Automatic validation for required fields and multiline inputs

## Configuration

Settings are persisted in `~/.openvino_genai_chat/config.json`:

```json
{
  "model_path": "/path/to/model",
  "device": "CPU",
  "max_new_tokens": 4096,
  "theme": "dark",
  "use_thinking": false,
  "auto_save_interval": 5
}
```

Conversations are stored in `~/.openvino_genai_chat/conversations/` as individual JSON files.

## Development

### Setting Up Development Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/ --cov=openvino_genai_chat  # With coverage
```

### Code Quality

```bash
black openvino_genai_chat/  # Format code
flake8 openvino_genai_chat/  # Lint
mypy openvino_genai_chat/    # Type checking
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Uses [OpenVINO](https://github.com/openvinotoolkit/openvino) for model inference
- Markdown rendering with [python-markdown](https://python-markdown.github.io/)

## Troubleshooting

### Model Not Found Error

Ensure your OpenVINO model path is correct:
1. Click "⚙ Config"
2. Use "Browse..." to select the model directory
3. The directory should contain model files (bin, xml, etc.)

### GPU Not Available

If GPU device selection fails:
1. Check that your OpenVINO installation supports GPU
2. Verify GPU drivers are properly installed
3. Fall back to CPU in configuration

### Slow Performance

- Reduce `max_new_tokens` to generate shorter responses faster
- Use CPU device for testing (GPU requires proper setup)
- Close other applications to free system memory

## Future Enhancements

- [ ] Security hardening (input sanitization, encryption)
- [ ] SQLite database migration
- [ ] Advanced template customization UI
- [ ] Multi-turn context management
- [ ] Response filtering and quality metrics
- [ ] Plugin system for custom templates
- [ ] Web deployment option
- [ ] Batch processing for multiple prompts
