from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from pages.base_page import BasePage
from test_data.test_constants import BASE_URL

class RegisterDoctorPage(BasePage):
    """Page Object representing the Doctor Registration page."""
    
    FULL_NAME_INPUT = (By.ID, "fullName")
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SPECIALIZATION_SELECT = (By.ID, "specialization")
    EXPERIENCE_INPUT = (By.ID, "experienceYears")
    CLINIC_ADDRESS_INPUT = (By.ID, "clinicAddress")
    SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit']")
    
    def navigate(self):
        """Navigate directly to the doctor registration page."""
        self.driver.get(f"{BASE_URL}/doctor/register")
        return self
        
    def register_doctor(self, full_name, email, password, specialization, experience_years, clinic_address):
        """Fill in doctor registration details and submit."""
        self.type(self.FULL_NAME_INPUT, full_name)
        self.type(self.EMAIL_INPUT, email)
        self.type(self.PASSWORD_INPUT, password)
        
        # Select specialization from drop-down
        spec_element = self.find_visible_element(self.SPECIALIZATION_SELECT)
        select = Select(spec_element)
        select.select_by_value(specialization)
        
        self.type(self.EXPERIENCE_INPUT, str(experience_years))
        self.type(self.CLINIC_ADDRESS_INPUT, clinic_address)
        self.click(self.SUBMIT_BUTTON)
