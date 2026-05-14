# OpenVINO GenAI Chat Application

A professional PyQt5-based chat interface for local OpenVINO model inference with real-time streaming, conversation persistence, and template support.

## Features

- **Real-time Streaming**: Watch model responses appear character-by-character as they're generated.
- **Speech-to-Text (STT)**:
  - **Universal Language Support**: Transcribe audio in all **99 languages** supported by multilingual Whisper models.
  - **Auto-Detection & Translation**: Automatically detect the input language or translate foreign audio directly into English.
  - **Broad Format Support**: Process `.mp3`, `.m4a`, `.mp4`, `.wav`, and more via FFmpeg integration.
  - **Live Progress**: Watch words appear in real-time as the audio is processed.
- **Enhanced Model Management**:
  - **Live Download Logs**: View a real-time log stream from Hugging Face during model downloads, providing detailed file-by-file progress and speeds.
  - **Robust Generation Control**: Instantly cancel text generation with a dedicated button and configurable safety timeouts to prevent UI freezes.
- **Conversation Persistence**: Automatically save all conversations to disk and revisit them anytime with a searchable sidebar.
- **Template System**: Streamline repetitive workflows with user-defined custom templates and field validation.
- **Modern UI/UX**:
  - **Think/No-Think Toggle**: Switch between reasoning-intensive (`/think`) and standard (`/no_think`) modes with a single click.
  - **High-Contrast Design**: Professional dark/light themes with improved visibility for all interactive elements.
  - **Markdown & Code**: Full markdown rendering with support for code blocks, tables, and lists.
- **Stability & Performance**:
  - **Windowless GUI Support**: Fully optimized for launching as a background/windowless process without terminal crashes.
  - **Asynchronous Architecture**: All heavy operations (inference, STT, downloads) run in background threads to keep the UI perfectly responsive.

## Why Local PyQt5? (Security & Privacy)

While web-based alternatives like Streamlit or OpenWebUI are popular, this native desktop application offers several critical cybersecurity advantages:

- **Zero Network Exposure**: Unlike web-based interfaces that open local ports (`localhost:8501`, etc.), this application has no listening network-bound ports. Since it is a self-contained process, it is immune to unauthorized local network access or Cross-Site Request Forgery (CSRF).
- **Reduced Attack Surface**: By avoiding browser engines, we eliminate entire categories of common web vulnerabilities such as Cross-Site Scripting (XSS), insecure cookie management, and data interception via malicious browser extensions.
- **Process Isolation**: The OpenVINO inference engine runs within the application's own memory space. There is no need for a separate Model Server which would require an open gRPC/REST API port.
- **Data Sovereignty**: Your conversations and settings never leave your machine. The app does not rely on external database servers, cloud backends, or third-party CDNs.

## Youtube Video
Demo video link : ([https://www.youtube.com/watch?v=ldvx83SdIkY](https://www.youtube.com/watch?v=ldvx83SdIkY))

## Getting Started

On your first launch, the application will automatically download the **Phi-3.5-mini-instruct-int4-ov** model from Hugging Face (~2GB) if no other model is configured. Please ensure you have an active internet connection for this initial setup.

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

### From Source
1. Clone the repository and navigate to it:
```bash
git clone https://github.com/yourusername/pyqt5-openvino-chat-app.git
cd pyqt5-openvino-chat-app
```

2. Setup virtual environment and install:
```bash
python -m venv venv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate

pip install -e .
openvino-chat
```

### Install FFmpeg (Windows)
For Speech-to-Text to support compressed formats:
```powershell
winget install "FFmpeg (Essentials Build)"
```

## Usage

1. **Configure the Model**:
   - Click "⚙ Config" to set model path, device (CPU/GPU), and token limits.
   - Adjust the **Cancel Wait (ms)** setting if you encounter freezes on slow hardware.

2. **Download Models**:
   - Enter a Hugging Face Repo ID in the Config dialog.
   - Watch the **Live Log Stream** for detailed download progress.

3. **Inference Modes**:
   - Toggle the **/think** button to enable reasoning-intensive generation.
   - Use the sidebar to search or load previous conversations.

4. **Speech-to-Text**:
   - Click "🎙 STT" and select an audio/video file.
   - Choose from all **99 supported languages** or use "Auto Detect".
   - Select "Translate to English" if you need translation for foreign audio.
   - Click "▶ Transcribe" and watch the streaming results.

5. **Keyboard Shortcuts**:
   - `Ctrl+N`: New Chat
   - `Enter`: Send Message
   - `Shift+Enter`: New Line in input box
   - `Ctrl+C`: Copy selected text

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
