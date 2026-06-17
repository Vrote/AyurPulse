from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from test_data.test_constants import BASE_URL

class LoginPage(BasePage):
    """Page Object representing the User/Doctor Login page."""
    
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit']")
    
    def navigate(self):
        """Navigate to the login page directly."""
        self.driver.get(f"{BASE_URL}/login")
        return self
        
    def login(self, email, password):
        """Perform login action."""
        self.type(self.EMAIL_INPUT, email)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
