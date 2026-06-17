from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class BasePage:
    """Base class that all other Page Objects inherit from, providing reusable helper methods."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 30)
        self.scan_wait = WebDriverWait(self.driver, 120)  # Extended wait for ML diagnostics
        
    def find_element(self, locator):
        """Wait for and return element presence in DOM."""
        return self.wait.until(EC.presence_of_element_located(locator))
        
    def find_visible_element(self, locator):
        """Wait for and return element visibility."""
        return self.wait.until(EC.visibility_of_element_located(locator))
        
    def find_clickable_element(self, locator):
        """Wait for and return element clickability."""
        return self.wait.until(EC.element_to_be_clickable(locator))
        
    def click(self, locator):
        """Standard explicit-wait click using javascript fallback to bypass overlay/timing issues."""
        element = self.find_clickable_element(locator)
        self.driver.execute_script("arguments[0].click();", element)
        
    def type(self, locator, text):
        """Clear and type text into an input field after ensuring visibility."""
        element = self.find_visible_element(locator)
        element.clear()
        element.send_keys(text)
        
    def get_text(self, locator):
        """Get element text after ensuring visibility."""
        return self.find_visible_element(locator).text
        
    def wait_for_url(self, url_part):
        """Explicitly wait for the browser URL to contain a specific substring."""
        return WebDriverWait(self.driver, 30).until(EC.url_contains(url_part))
