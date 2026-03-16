# app/utils/image_preprocess.py
from torchvision import transforms
from PIL import Image, UnidentifiedImageError
import torch

# Image transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])

# Device configuration
from app.models.prediction_model import device


def preprocess_image(image_path: str) -> torch.Tensor:
    """
    Preprocess an image for model prediction.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        torch.Tensor: Preprocessed image tensor ready for model input.
    
    Raises:
        ValueError: If the image cannot be opened or is invalid.
    """
    try:
        # Open image and convert to RGB
        image = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        raise ValueError(f"Image file not found: {image_path}")
    except UnidentifiedImageError:
        raise ValueError(f"Cannot identify image file: {image_path}")
    except Exception as e:
        raise ValueError(f"Error loading image {image_path}: {e}")

    # Apply transforms
    image_tensor = transform(image)

    # Add batch dimension and move to device
    return image_tensor.unsqueeze(0).to(device)