import os
import time
from PIL import Image
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from test_data.test_constants import SKIN_IMAGE_PATH

def create_dummy_skin_image():
    """
    Checks if a real skin/face image is available at SKIN_IMAGE_PATH.
    If yes, returns the absolute path to that image.
    If no, generates a temporary red fallback image (PNG) in the workspace and returns its path.
    """
    if SKIN_IMAGE_PATH and os.path.isfile(SKIN_IMAGE_PATH):
        print(f"[*] Found real skin image at: {SKIN_IMAGE_PATH}")
        return os.path.abspath(SKIN_IMAGE_PATH)
    
    # Fallback to creating a dummy image
    img_path = os.path.abspath("temp_face.png")
    if not os.path.exists(img_path):
        img = Image.new("RGB", (200, 200), color="red")
        img.save(img_path)
        print(f"[*] SKIN_IMAGE_PATH not found or invalid. Created temporary dummy skin image at: {img_path}")
    return img_path

class ElementWait:
    """Reusable explicit wait wrappers for elements to avoid using time.sleep."""
    
    @staticmethod
    def wait_for_visibility(driver, locator, timeout=30):
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    
    @staticmethod
    def wait_for_presence(driver, locator, timeout=30):
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        
    @staticmethod
    def wait_for_clickable(driver, locator, timeout=30):
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        
    @staticmethod
    def wait_for_url_contains(driver, url_substring, timeout=30):
        return WebDriverWait(driver, timeout).until(
            EC.url_contains(url_substring)
        )
        
    @staticmethod
    def wait_for_invisibility(driver, locator, timeout=30):
        return WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )
