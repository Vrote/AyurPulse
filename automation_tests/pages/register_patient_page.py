from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from test_data.test_constants import BASE_URL

class RegisterPatientPage(BasePage):
    """Page Object representing the Patient Registration page."""
    
    FULL_NAME_INPUT = (By.ID, "fullName")
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit']")
    
    def navigate(self):
        """Navigate directly to the patient registration page."""
        self.driver.get(f"{BASE_URL}/register")
        return self
        
    def register_patient(self, full_name, email, password):
        """Fill in patient details and submit."""
        self.type(self.FULL_NAME_INPUT, full_name)
        self.type(self.EMAIL_INPUT, email)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
