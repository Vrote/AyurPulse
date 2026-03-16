# app/models/prediction_model.py
import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Number of classes in the model
num_classes = 5

# Project root path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default model path
MODEL_PATH = BASE_DIR / "saved_models" / "face_skin_disease_model.pth"


def load_model(model_path: Path = MODEL_PATH):
    """
    Load the pretrained EfficientNet model for skin disease classification.
    Args:
        model_path (Path): Path to the .pth model file.
    Returns:
        model: PyTorch model ready for inference.
    Raises:
        FileNotFoundError: If the model file does not exist.
        RuntimeError: If model weights cannot be loaded.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    try:
        # Initialize EfficientNet-B2 model
        model = models.efficientnet_b2(weights=None)

        # Replace classifier with number of classes
        model.classifier[1] = nn.Linear(
            model.classifier[1].in_features,
            num_classes
        )

        # Load trained weights
        state_dict = torch.load(model_path, map_location=device)
        model.load_state_dict(state_dict)

        # Move to device and set evaluation mode
        model.to(device)
        model.eval()

        return model

    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")