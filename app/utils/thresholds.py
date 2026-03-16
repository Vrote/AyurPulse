# app/utils/thresholds.py
from typing import List

# List of classes predicted by the model
class_names: List[str] = ['acne', 'blackheads', 'dark spots', 'pores', 'wrinkles']

# Confidence thresholds
# Diseases other than wrinkles
disease_threshold: float = 88.0

# Wrinkle-specific threshold
wrinkle_threshold: float = 96.0

"""
Usage:
- If predicted probability >= threshold, the class is considered detected.
- disease_threshold applies to all classes except 'wrinkles'.
- wrinkle_threshold applies only to 'wrinkles'.
"""