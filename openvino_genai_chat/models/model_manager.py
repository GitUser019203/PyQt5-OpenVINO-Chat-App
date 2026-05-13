"""Global model manager - initializes before PyQt5 starts."""

from pathlib import Path
from typing import Optional, Callable
import io
import threading
import sys
import signal
from huggingface_hub import snapshot_download
from tqdm import tqdm
from ..utils.logger import setup_logger
from ..utils.constants import Device
from .openvino_wrapper import OpenVINOWrapper


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
            progress = int((self.n / self.total) * 100)
            self._callback(progress)

    def close(self):
        if self._callback:
            self._callback(100)
        super().close()


logger = setup_logger(__name__)


def timeout_handler(signum, frame):
    """Handle initialization timeout."""
    logger.error("⏱ Model initialization timeout - process exceeded 300 seconds")
    sys.exit(1)


class ModelManager:
    """Singleton model manager initialized before PyQt5."""

    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize the model manager."""
        self.model: Optional[OpenVINOWrapper] = None
        self.error: Optional[str] = None
        self.loading = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def initialize(self, model_path: Path, device: Device, max_tokens: int) -> bool:
        """
        Initialize the model synchronously.

        Args:
            model_path: Path to OpenVINO model
            device: Device (CPU/GPU)
            max_tokens: Max tokens

        Returns:
            True if successful, False if failed
        """
        if self.loading:
            logger.warning("Model initialization already in progress")
            return False

        if self.model is not None:
            logger.warning("Model already initialized")
            return True

        self.loading = True
        self.error = None

        try:
            logger.info("=" * 70)
            logger.info("GLOBAL MODEL INITIALIZATION (BEFORE PyQt5)")
            logger.info("=" * 70)
            logger.info(f"Model path: {model_path}")
            logger.info(f"Device: {device.value}")
            logger.info(f"Max tokens: {max_tokens}")
            logger.info("Initializing OpenVINO LLMPipeline...")

            try:
                self.model = OpenVINOWrapper(model_path, device, max_tokens)
            finally:
                pass

            logger.info("✓ Model initialized successfully BEFORE PyQt5 started")
            logger.info("=" * 70)
            self.loading = False
            return True

        except Exception as e:
            self.loading = False
            error_msg = f"Failed to initialize model: {e}"
            logger.error(f"✗ {error_msg}")
            logger.error("=" * 70)
            logger.exception("Full traceback:")
            self.error = error_msg
            self.model = None
            return False

    def get_model(self) -> Optional[OpenVINOWrapper]:
        """Get the initialized model."""
        return self.model

    def is_ready(self) -> bool:
        """Check if model is ready."""
        return self.model is not None and not self.loading

    def get_error(self) -> Optional[str]:
        """Get initialization error if any."""
        return self.error

    def download_model(self, repo_id: str, target_dir: Path, progress_callback: Optional[Callable[[int], None]] = None) -> Path:
        """
        Download a model from Hugging Face or return local path if already exists.

        Args:
            repo_id: Hugging Face repository ID
            target_dir: Target directory for downloading
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded model
        """
        local_path = target_dir / repo_id.replace("/", "--")

        # If it's already there and appears valid, skip download
        is_valid = (local_path / "openvino_model.xml").exists()
        if local_path.exists() and is_valid:
            logger.info(f"Model {repo_id} already exists locally. Skipping download check.")
            return local_path

        logger.info(f"Downloading model from HF: {repo_id}")

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

        return Path(model_path)
