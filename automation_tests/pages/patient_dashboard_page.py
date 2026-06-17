import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage

class PatientDashboardPage(BasePage):
    """Page Object representing the Patient Dashboard with various workspace actions."""
    
    # Header & Welcome
    NAMASTE_HEADER = (By.XPATH, "//*[contains(text(), 'Namaste')]")
    SIGN_OUT_BUTTON = (By.XPATH, "//button[contains(text(), 'Sign Out')]")
    
    # Skin Scan
    FILE_INPUT = (By.XPATH, "//input[@type='file']")
    ANALYZE_BUTTON = (By.XPATH, "//button[contains(text(), 'Analyze Skin Condition')]")
    SCAN_SUCCESS_MSG = (By.XPATH, "//*[contains(text(), 'Skin Diagnostic Successful!')]")
    
    # Prakriti Quiz
    CONTINUE_PROFILE_BUTTON = (By.XPATH, "//button[contains(text(), 'Continue to Profile Specifics')]")
    
    # Customization Settings
    STRESS_CHECKBOX = (By.XPATH, "//button[contains(., 'High Stress Environment')]/input")
    GENERATE_PLAN_BUTTON = (By.XPATH, "//button[contains(text(), 'Generate 7-Day Plan')]")
    PENDING_VETTING_MSG = (By.XPATH, "//*[contains(text(), 'Pending Doctor Vetting')]")
    
    # Saved Plans
    SAVED_PLANS_TAB = (By.XPATH, "//button[contains(text(), 'My Saved Plans')]")
    VERIFIED_BADGE = (By.XPATH, "//*[contains(text(), 'Verified')]")
    VIEW_SCHEDULE_BUTTON = (By.XPATH, "//button[contains(text(), 'View Full Schedule')]")
    CLOSE_MODAL_BUTTON = (By.XPATH, "//*[contains(text(), '✕')]")
    
    # Nearby Shops
    NEARBY_SHOPS_TAB = (By.XPATH, "//button[contains(text(), 'Nearby Ayurvedic Shops')]")
    MANUAL_COORDS_BUTTON = (By.XPATH, "//button[contains(text(), 'Enter Coordinates Manually')]")
    LATITUDE_INPUT = (By.XPATH, "//input[@placeholder='e.g. 18.5204']")
    LONGITUDE_INPUT = (By.XPATH, "//input[@placeholder='e.g. 73.8567']")
    SEARCH_COORDS_BUTTON = (By.XPATH, "//button[contains(text(), 'Search coordinates')]")
    DIRECTIONS_TEXT = (By.XPATH, "//*[contains(text(), 'Directions')]")

    def verify_on_dashboard(self):
        """Confirm user has loaded into dashboard successfully."""
        self.find_visible_element(self.NAMASTE_HEADER)
        return self
        
    def perform_skin_scan(self, image_path):
        """Upload image to hidden input file dialog and start analysis."""
        file_input = self.find_element(self.FILE_INPUT)
        file_input.send_keys(image_path)
        
        # Click analyze and await ML response
        self.click(self.ANALYZE_BUTTON)
        self.scan_wait.until(EC.presence_of_element_located(self.SCAN_SUCCESS_MSG))
        return self
        
    def answer_prakriti_quiz(self, answers_indices):
        """
        Clicks one radio button option for each quiz category.
        answers_indices: positional list of 1-indexed integers indicating which radio options to click.
        """
        # Ensure radio options are visible and page settles
        self.find_visible_element((By.XPATH, "//input[@type='radio']"))
        time.sleep(1) # Settle questionnaire loading
        
        for index in answers_indices:
            radio_xpath = f"(//input[@type='radio'])[{index}]"
            radio = self.wait.until(EC.presence_of_element_located((By.XPATH, radio_xpath)))
            self.driver.execute_script("arguments[0].click();", radio)
            time.sleep(0.3)
            
        self.click(self.CONTINUE_PROFILE_BUTTON)
        return self
        
    def configure_profile_and_generate_plan(self, skin_type, age_group, season, lifestyle_stress=True):
        """Customize skin type, age, season and trigger AI generation of 7-day schedule."""
        # Locate Select components on profile screen
        selects = self.wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
        
        skin_select = Select(selects[0])
        skin_select.select_by_value(skin_type)
        
        age_select = Select(selects[1])
        age_select.select_by_value(age_group)
        
        season_select = Select(selects[2])
        season_select.select_by_value(season)
        
        if lifestyle_stress:
            self.click(self.STRESS_CHECKBOX)
            
        self.click(self.GENERATE_PLAN_BUTTON)
        self.wait.until(EC.presence_of_element_located(self.PENDING_VETTING_MSG))
        return self
        
    def verify_vetted_plan(self, expected_notes):
        """Navigate to plans history tab and verify custom doctor note injection within schedule modal."""
        self.click(self.SAVED_PLANS_TAB)
        self.find_visible_element(self.VERIFIED_BADGE)
        
        self.click(self.VIEW_SCHEDULE_BUTTON)
        
        # Verify custom advice inside details modal
        notes_xpath = f"//*[contains(text(), '{expected_notes}')]"
        self.wait.until(EC.presence_of_element_located((By.XPATH, notes_xpath)))
        
        # Close details modal
        self.click(self.CLOSE_MODAL_BUTTON)
        return self
        
    def find_nearby_shops(self, latitude, longitude):
        """Use manual coordinate submission to find local Ayurvedic clinics."""
        self.click(self.NEARBY_SHOPS_TAB)
        self.click(self.MANUAL_COORDS_BUTTON)
        
        self.type(self.LATITUDE_INPUT, str(latitude))
        self.type(self.LONGITUDE_INPUT, str(longitude))
        self.click(self.SEARCH_COORDS_BUTTON)
        
        # Confirm OpenStreetMap geolocation query returned results
        self.find_visible_element(self.DIRECTIONS_TEXT)
        return self
        
    def sign_out(self):
        """Trigger sign out and await redirect to login page."""
        self.click(self.SIGN_OUT_BUTTON)
        self.wait_for_url("/login")
        return self
