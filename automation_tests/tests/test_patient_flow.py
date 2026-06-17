import random
import pytest
from pages.register_patient_page import RegisterPatientPage
from pages.login_page import LoginPage
from pages.patient_dashboard_page import PatientDashboardPage

@pytest.mark.patient
class TestPatientFlow:
    """Comprehensive functional verification of Patient flows: Scan, Quiz, Plan Gen, Shops Geolocation."""
    
    @pytest.fixture(autouse=True)
    def setup_credentials(self):
        rand_id = random.randint(10000, 99999)
        self.email = f"patient_flow_{rand_id}@ayurtest.com"
        self.password = "Password@123"
        self.name = f"Patient Flow User {rand_id}"
        
    def test_complete_patient_workflow(self, driver, skin_image):
        """Validates skin diagnostic scan upload, quiz submission, plan generation, and pharmacy geosearch."""
        register_page = RegisterPatientPage(driver)
        login_page = LoginPage(driver)
        dashboard_page = PatientDashboardPage(driver)
        
        # 1. Register & Login
        register_page.navigate().register_patient(self.name, self.email, self.password)
        login_page.navigate().login(self.email, self.password)
        dashboard_page.verify_on_dashboard()
        
        # 2. Perform skin scan using image file
        dashboard_page.perform_skin_scan(skin_image)
        
        # 3. Answer 6 Prakriti Quiz questions
        # Positional index of radio buttons for medium frame, strong hunger, sound sleep, hot feeling, burning digestion, focused mood.
        dashboard_page.answer_prakriti_quiz([1, 5, 8, 11, 14, 17])
        
        # 4. Personalize options and generate plan
        dashboard_page.configure_profile_and_generate_plan(
            skin_type="combination",
            age_group="21-30",
            season="summer",
            lifestyle_stress=True
        )
        
        # 5. Geosearch nearby Ayurvedic pharmacies using coordinates
        dashboard_page.find_nearby_shops(latitude=18.5204, longitude=73.8567)
        
        # 6. Clean sign out
        dashboard_page.sign_out()
        
        print("[+] Patient complete functional workflow completed successfully.")
