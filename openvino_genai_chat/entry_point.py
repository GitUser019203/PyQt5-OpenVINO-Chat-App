"""OpenVINO GenAI Chat Application - Entry Point"""

import sys
from openvino_genai_chat.utils.logger import setup_logger
import openvino_genai as ov_genai

from openvino_genai_chat.utils.settings import SettingsManager

def start_app():
    # PHASE 1: Initialize model BEFORE PyQt5 starts
    logger = setup_logger(__name__)
    logger.info("\n[PHASE 1] Initializing OpenVINO model (BEFORE PyQt5)...")
    settings_mgr = SettingsManager()
    model_path = settings_mgr.get_model_path()
    device = settings_mgr.get_device()
    
    # Check if model exists
    if not (model_path / "openvino_model.xml").exists():
        from openvino_genai_chat.utils.constants import INITIAL_MODEL_ID, APP_DIR
        from huggingface_hub import snapshot_download
        
        # If the current path is the default one, or if it simply doesn't exist,
        # we treat this as a first-run or missing-model scenario.
        logger.info(f"🚀 Initial startup check: Model not found at {model_path}")
        logger.info(f"📥 Downloading default model '{INITIAL_MODEL_ID}' to get you started...")
        
        try:
            # Ensure the directory exists
            model_path.mkdir(parents=True, exist_ok=True)
            
            # Download from Hugging Face
            # This will show a progress bar in the console
            snapshot_download(
                repo_id=INITIAL_MODEL_ID,
                local_dir=model_path,
                local_dir_use_symlinks=False
            )
            logger.info(f"✅ Successfully downloaded {INITIAL_MODEL_ID}")
            logger.info(f"📍 Model saved to: {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to download initial model: {e}")
            logger.error("Please ensure you have an active internet connection.")
            logger.error(f"You can also manually download a model and place it in {model_path}")
            # We don't exit here, we let LLMPipeline try to load it (and fail) 
            # to provide standard error handling if the download was partial but valid.
    
    try:
        logger.info(f"Loading OpenVINO GenAI pipeline from {model_path}...")
        pipe = ov_genai.LLMPipeline(
                    models_path=model_path.as_posix(),
                    device=device.value,
                )
        logger.info("✓ Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenVINO pipeline: {e}")
        logger.error("-" * 70)
        logger.error("POSSIBLE SOLUTIONS:")
        logger.error(f"1. Ensure the model directory contains 'openvino_model.xml': {model_path}")
        logger.error(f"2. Check if your device '{device.value}' is supported.")
        logger.error("3. If this is the first run, ensure your internet connection is active for the auto-download.")
        logger.error("-" * 70)
        sys.exit(1)

    from openvino_genai_chat.gui.main_window import main
    main(pipe, logger)
