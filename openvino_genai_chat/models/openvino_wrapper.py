"""OpenVINO model wrapper with streaming support."""

from asyncio.windows_utils import pipe
from pathlib import Path
from typing import Callable, Generator, Optional
from click import prompt
import openvino_genai as ov_genai
from twine.cli import args
from ..utils.logger import setup_logger
from ..utils.constants import Device

logger = setup_logger(__name__)


class OpenVINOWrapper:
    """
    Wrapper around OpenVINO GenAI LLMPipeline.
    Handles model initialization, device selection, and streaming inference.
    """
    
    def __init__(
        self,
        model_path: Path,
        device: Device = Device.CPU,
        max_new_tokens: int = 4096,
        dont_initialize_model: bool = False,
    ):
        """
        Initialize OpenVINO model wrapper.
        
        Args:
            model_path: Path to OpenVINO model directory
            device: Device to run inference on (CPU/GPU)
            max_new_tokens: Maximum tokens to generate
            
        Raises:
            FileNotFoundError: If model path doesn't exist
            RuntimeError: If model initialization fails
        """
        self.model_path = Path(model_path)
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.pipeline: Optional[ov_genai.LLMPipeline] = None
        self.chat_active = False
        self._stop_flag = False
        
        if not dont_initialize_model:
            self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the OpenVINO pipeline with retry logic."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model path not found: {self.model_path}"
            )
        
        try:
            logger.info(
                f"Attempting to initialize OpenVINO model from {self.model_path} "
                f"on {self.device.value}"
            )
            
            # Try primary initialization method
            self.pipeline = ov_genai.LLMPipeline(
                str(self.model_path),
                self.device.value
            )
            
            logger.info("✓ OpenVINO model initialized successfully with primary method")
        
        except Exception as e:
            logger.warning(f"Primary initialization failed: {e}, attempting alternative method...")
            try:
                # Fallback: try with Path object directly and device.name
                logger.info("Attempting fallback initialization with device.name...")
                self.pipeline = ov_genai.LLMPipeline(
                    self.model_path,
                    self.device.name,
                )
                logger.info("✓ OpenVINO model initialized successfully with fallback method")
            
            except Exception as fallback_e:
                error_msg = f"Both initialization methods failed. Primary: {e}, Fallback: {fallback_e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    def start_chat(self) -> None:
        """Start a chat session."""
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")
        
        self.pipeline.start_chat()
        self.chat_active = True
        logger.debug("Chat session started")
    
    def finish_chat(self) -> None:
        """Finish the current chat session."""
        if not self.pipeline:
            return
        
        self.pipeline.finish_chat()
        self.chat_active = False
        logger.debug("Chat session finished")

    def stop_generation(self) -> None:
        """Signal the streaming generation loop to stop after the current token."""
        self._stop_flag = True
        logger.debug("Stop generation flag set")
    
    def generate_streaming(
        self,
        prompt: str,
        callback: Callable[[str], None],
    ) -> str:
        """
        Generate response with streaming.
        Calls callback for each chunk of generated text.
        
        Args:
            prompt: Input prompt
            callback: Function called with each text chunk
            
        Returns:
            Full generated response
        """
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")
        
        logger.debug(f"Generating response for prompt: {prompt[:100]}...")
        
        full_response = []
        self._stop_flag = False  # Reset before each generation
        
        try:
            # Use the streamer callback pattern
            def streamer(subword: str) -> ov_genai.StreamingStatus:
                """Stream callback for token generation."""
                if self._stop_flag:
                    return ov_genai.StreamingStatus.STOP
                callback(subword)
                full_response.append(subword)
                return ov_genai.StreamingStatus.RUNNING
            
            # Generate with streaming
            self.pipeline.generate(
                prompt,
                streamer=streamer,
                max_new_tokens=self.max_new_tokens,
                echo=False,  # Don't echo the input prompt
            )
            
            result = "".join(full_response)
            logger.debug(f"Generated response: {len(result)} chars")
            return result
        
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise
    
    def generate(self, prompt: str) -> str:
        """
        Generate response without streaming.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
        """
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")
        
        logger.debug(f"Generating response (non-streaming): {prompt[:100]}...")
        
        try:
            output = self.pipeline.generate(
                prompt,
                max_new_tokens=self.max_new_tokens,
                echo=False,
            )
            
            result = str(output)
            logger.debug(f"Generated response: {len(result)} chars")
            return result
        
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if pipeline is ready for inference."""
        return self.pipeline is not None
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_path": str(self.model_path),
            "device": self.device.value,
            "max_new_tokens": self.max_new_tokens,
            "chat_active": self.chat_active,
        }
