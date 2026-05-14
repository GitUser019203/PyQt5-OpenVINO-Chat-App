"""Speech-to-Text manager using OpenVINO GenAI."""

import os
import io
import sys
import wave
import platform
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, Callable
import openvino_genai as ov_genai
from huggingface_hub import snapshot_download
from tqdm import tqdm
from ..utils.logger import setup_logger
from ..utils.settings import SettingsManager

# On Windows, prevent console windows from popping up when pydub calls ffmpeg
if platform.system() == "Windows":
    CREATE_NO_WINDOW = 0x08000000
    _original_popen = subprocess.Popen
    def _patched_popen(*args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = CREATE_NO_WINDOW
        return _original_popen(*args, **kwargs)
    subprocess.Popen = _patched_popen

logger = setup_logger(__name__)

class TqdmProgress(tqdm):
    """Wrapper for tqdm to report progress via callback.

    Safely redirects tqdm output to a null sink when sys.stdout is None,
    which happens when the app is launched as a windowless GUI process
    (e.g. via the openvino-chat entry point on Windows).
    """
    def __init__(self, *args, **kwargs):
        self._callback = kwargs.pop("progress_callback", None)
        # When running as a GUI app sys.stdout may be None; tqdm would crash
        # trying to write to it. Redirect to a null sink in that case.
        if sys.stdout is None:
            kwargs.setdefault("file", io.StringIO())
        super().__init__(*args, **kwargs)

    def update(self, n=1):
        super().update(n)
        if self._callback and self.total:
            # Report percentage
            progress = int((self.n / self.total) * 100)
            self._callback(progress)

    def close(self):
        if self._callback:
            self._callback(100)
        super().close()

class STTStreamer(ov_genai.StreamerBase):
    """Streamer for real-time transcription feedback."""
    def __init__(self, tokenizer: ov_genai.Tokenizer, callback: Callable[[str], bool]):
        super().__init__()
        self.tokenizer = tokenizer
        self.callback = callback

    def put(self, token_id: int):
        # Decode token to text using the tokenizer
        try:
            text = self.tokenizer.decode([token_id])
            if text:
                # Some tokenizers return the token ID string for special tokens
                # We want to filter those out or handle them
                self.callback(text)
        except Exception:
            pass
        return ov_genai.StreamingStatus.RUNNING

    def write(self, text):
        """Called with the decoded text fragments or raw tokens."""
        try:
            if text:
                if isinstance(text, list):
                    if len(text) > 0 and isinstance(text[0], int):
                        # It's a list of token IDs! Decode them.
                        text = self.tokenizer.decode(text)
                    else:
                        # It's a list of something else (strings?), join them
                        text = "".join(str(item) for item in text)
                
                # Final check to make sure we are sending a string
                self.callback(str(text))
        except Exception:
            pass
        return ov_genai.StreamingStatus.RUNNING

    def end(self):
        """Called when generation is finished."""
        pass

class STTManager:
    """Manages downloading and running OpenVINO STT models."""
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize STT manager.
        
        Args:
            models_dir: Directory to store downloaded models
        """
        if models_dir is None:
            # Use SettingsManager to get the base model directory from config
            settings = SettingsManager()
            text_model_path = settings.get_model_path()
            
            # Use the same base directory as the text generation models
            # Standard structure is models/OpenVINO/model_name
            # We will use models/STT
            if "OpenVINO" in text_model_path.parts:
                # Find the index of 'OpenVINO' and get the path up to that
                idx = text_model_path.parts.index("OpenVINO")
                base_dir = Path(*text_model_path.parts[:idx])
                self.models_dir = base_dir / "STT"
            else:
                # Fallback to the same parent directory if structure is different
                self.models_dir = text_model_path.parent.parent / "STT"
        else:
            self.models_dir = Path(models_dir)
            
        self.models_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"STT models directory set to: {self.models_dir}")
        self.pipeline: Optional[ov_genai.WhisperPipeline] = None
        self.tokenizer: Optional[ov_genai.Tokenizer] = None
        self.current_model_path: Optional[Path] = None

    def list_local_models(self) -> list[dict]:
        """
        List models already downloaded on disk.
        
        Returns:
            List of dictionaries with model info (name, path)
        """
        local_models = []
        if not self.models_dir.exists():
            return local_models
            
        for item in self.models_dir.iterdir():
            if item.is_dir():
                # Check if it's a valid OpenVINO model directory (standard or Whisper)
                is_valid = (
                    (item / "openvino_encoder_model.xml").exists() or 
                    (item / "openvino_model.xml").exists()
                )
                if is_valid:
                    # Name is repo ID with -- replaced by /
                    name = item.name.replace("--", "/")
                    local_models.append({
                        "name": name,
                        "path": item
                    })
        return local_models

    def download_model(self, repo_id: str, progress_callback: Optional[Callable[[int], None]] = None) -> Path:
        """
        Download a model from Hugging Face or return local path if already exists.
        
        Args:
            repo_id: Hugging Face repository ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to the downloaded model
        """
        local_path = self.models_dir / repo_id.replace("/", "--")
        
        # If it's already there and appears valid, skip download
        is_valid = (
            (local_path / "openvino_encoder_model.xml").exists() or 
            (local_path / "openvino_model.xml").exists()
        )
        if local_path.exists() and is_valid:
            logger.info(f"Model {repo_id} already exists locally. Skipping download check.")
            self.verify_model_files(local_path)
            return local_path

        logger.info(f"Downloading STT model from HF: {repo_id}")
        
        # Use a dynamic class to pass the callback while remaining a valid tqdm class
        class ProgressHandler(TqdmProgress):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, progress_callback=progress_callback, **kwargs)

        model_path = snapshot_download(
            repo_id=repo_id,
            local_dir=local_path,
            local_dir_use_symlinks=False,
            tqdm_class=ProgressHandler if progress_callback else None
        )
        
        target_path = Path(model_path)
        self.verify_model_files(target_path)
        return target_path

    def verify_model_files(self, model_path: Path) -> None:
        """
        Verify that .bin files in the model directory are not pickle files.
        
        Args:
            model_path: Path to the model directory
            
        Raises:
            SecurityError: If a suspicious file is found
        """
        for bin_file in model_path.glob("*.bin"):
            logger.debug(f"Verifying {bin_file.name}")
            with open(bin_file, "rb") as f:
                header = f.read(16)
                
            # Convert to hex string for logging and check
            hex_header = " ".join(f"{b:02X}" for b in header)
            logger.info(f"File Header for {bin_file.name}: {hex_header}")
            
            # Simple check: Pickle files usually start with 0x80
            if header and header[0] == 0x80:
                error_msg = f"Security Alert: {bin_file.name} appears to be a pickle file (starts with 0x80). Possible malicious code."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # The user's example shows a header of all zeros then 08 00 00 00
            # OpenVINO IR files usually have a specific structure.
            # If the header starts with 0x80, it's almost certainly a pickle.
            # We can also check for other pickle markers if needed.

    def load_model(self, model_path: Path, device: str = "CPU") -> bool:
        """
        Load an OpenVINO Whisper model.
        
        Args:
            model_path: Path to the model directory
            device: Device to run inference on
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Loading Whisper model from {model_path} on {device}")
            self.pipeline = ov_genai.WhisperPipeline(str(model_path), device)
            self.tokenizer = ov_genai.Tokenizer(str(model_path))
            self.current_model_path = model_path
            return True
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False

    def transcribe(self, audio_path: Path, streamer_callback: Optional[Callable[[str], bool]] = None, **kwargs) -> str:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the .mp3, .wav, .m4a, or .mp4 file
            streamer_callback: Optional callback for real-time text updates
            **kwargs: Additional generation config options (e.g. language="<|es|>", task="translate")
            
        Returns:
            Transcribed text
        """
        if self.pipeline is None:
            raise RuntimeError("Model not loaded")
            
        logger.info(f"Transcribing {audio_path}")
        
        audio_data = self._load_audio(audio_path)
        
        # Prepare streamer if callback provided
        streamer = None
        if streamer_callback and self.tokenizer:
            streamer = STTStreamer(self.tokenizer, streamer_callback)
            
        # Perform transcription
        result = self.pipeline.generate(audio_data, streamer=streamer, **kwargs)
        
        # Robust handling of different OpenVINO GenAI return types
        if isinstance(result, list):
            # If it's a list of ints (tokens), decode it
            if result and isinstance(result[0], int) and self.tokenizer:
                return self.tokenizer.decode(result)
            # If it's a list of objects with 'texts', take the first one
            if result and hasattr(result[0], 'texts'):
                return result[0].texts[0]
            # Otherwise return string representation
            return str(result)

        if hasattr(result, 'texts'):
            return result.texts[0]
            
        # Fallback for older or newer versions
        return str(result)

    def _load_audio(self, audio_path: Path) -> np.ndarray:
        """
        Load and preprocess audio file.
        Uses pydub if available, otherwise falls back to simple wave if it's a wav.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Numpy array of audio samples (float32, 16kHz, mono)
        """
        try:
            from pydub import AudioSegment
            
            # Load audio
            audio = AudioSegment.from_file(str(audio_path))
            
            # Convert to 16kHz, mono, 16-bit
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Get raw data and convert to numpy array
            samples = np.frombuffer(audio.raw_data, dtype=np.int16)
            
            # Convert to float32 and normalize to [-1, 1]
            return samples.astype(np.float32) / 32768.0
            
        except ImportError:
            logger.warning("pydub not installed. Falling back to wave (only supports .wav).")
            if audio_path.suffix.lower() != ".wav":
                raise ImportError("pydub is required for non-wav files (like .mp3, .m4a, .mp4)")
                
            with wave.open(str(audio_path), "rb") as wf:
                if wf.getnchannels() != 1 or wf.getframerate() != 16000 or wf.getsampwidth() != 2:
                    logger.warning("Wav file is not 16kHz mono 16-bit. Results may be poor.")
                
                samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                return samples.astype(np.float32) / 32768.0
