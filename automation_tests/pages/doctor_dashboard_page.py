from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class DoctorDashboardPage(BasePage):
    """Page Object representing the Ayurvedic Doctor Dashboard."""
    
    PRACTITIONER_HEADER = (By.XPATH, "//*[contains(text(), 'practitioner')]")
    REVIEW_BUTTON = (By.XPATH, "//button[contains(text(), 'Review & Edit')]")
    DOCTOR_NOTES_TEXTAREA = (By.ID, "doctorNotes")
    APPROVE_SAVE_BUTTON = (By.XPATH, "//button[contains(text(), 'Approve & Save Vetted Plan')]")
    SUCCESS_NOTIFICATION = (By.XPATH, "//*[contains(text(), 'vetted and updated successfully')]")
    SIGN_OUT_BUTTON = (By.XPATH, "//button[contains(text(), 'Sign Out')]")
    
    def verify_on_dashboard(self):
        """Confirm practitioner role has loaded doctor dashboard successfully."""
        self.find_visible_element(self.PRACTITIONER_HEADER)
        return self
        
    def review_and_approve_plan(self, custom_notes):
        """Clicks first plan on specialized queue table, injects notes and submits medical approval."""
        self.click(self.REVIEW_BUTTON)
        
        # Inject Custom Clinical Advice
        notes_area = self.find_visible_element(self.DOCTOR_NOTES_TEXTAREA)
        notes_area.clear()
        notes_area.send_keys(custom_notes)
        
        # Approve & Submit
        self.click(self.APPROVE_SAVE_BUTTON)
        self.wait.until(EC.presence_of_element_located(self.SUCCESS_NOTIFICATION))
        return self
        
    def sign_out(self):
        """Trigger sign out and await redirect to login page."""
        self.click(self.SIGN_OUT_BUTTON)
        self.wait_for_url("/login")
        return self
