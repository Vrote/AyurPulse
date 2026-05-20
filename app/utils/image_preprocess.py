from PIL import Image
from torchvision import transforms
import torch
import io


# Identical transform used during EfficientNet-B2 training — do not modify
TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """
    Convert raw image bytes to a normalised tensor ready for EfficientNet-B2.

    Args:
        image_bytes: Raw bytes of the uploaded image file.

    Returns:
        Tensor of shape (1, 3, 224, 224).

    Raises:
        ValueError: If the file cannot be read as a valid image.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise ValueError("Invalid image. Please upload a JPG or PNG file.")

    tensor = TRANSFORM(image)       # shape: (3, 224, 224)
    tensor = tensor.unsqueeze(0)    # shape: (1, 3, 224, 224)
    return tensor


def validate_image_size(file_size_bytes: int, max_mb: int = 5) -> None:
    """
    Raise ValueError if uploaded file exceeds the size limit.

    Args:
        file_size_bytes: Size of the file in bytes.
        max_mb: Maximum allowed size in megabytes.
    """
    max_bytes = max_mb * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise ValueError(f"Image too large. Maximum allowed size is {max_mb} MB.")