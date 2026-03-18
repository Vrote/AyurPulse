import torch
import torch.nn as nn
from torchvision import models
from app.config.settings import settings

# Singleton — model is loaded once when the app starts
_model = None
_device = None


def get_device() -> torch.device:
    """Return CUDA if available, else CPU."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model() -> tuple[nn.Module, torch.device]:
    """
    Load the trained EfficientNet-B2 model from disk.
    Uses a singleton so the model is only loaded once.

    Returns:
        Tuple of (model, device).

    Raises:
        FileNotFoundError: If the .pth file does not exist.
        RuntimeError: If the weights cannot be loaded into the architecture.
    """
    global _model, _device

    if _model is not None:
        return _model, _device

    _device = get_device()

    # Rebuild the same architecture used during training
    model = models.efficientnet_b2(weights=None)
    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features,
        settings.NUM_CLASSES
    )

    # Load saved weights
    try:
        state_dict = torch.load(settings.MODEL_PATH, map_location=_device)
        model.load_state_dict(state_dict)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Model file not found at '{settings.MODEL_PATH}'. "
            "Please place skin_disease_model.pth in the saved_models/ folder."
        )
    except RuntimeError as e:
        raise RuntimeError(f"Failed to load model weights: {e}")

    model = model.to(_device)
    model.eval()

    _model = model
    print(f"[AyurPulse] Model loaded on {_device}")
    return _model, _device