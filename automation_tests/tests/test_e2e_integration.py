import random
import pytest
from pages.register_patient_page import RegisterPatientPage
from pages.register_doctor_page import RegisterDoctorPage
from pages.login_page import LoginPage
from pages.patient_dashboard_page import PatientDashboardPage
from pages.doctor_dashboard_page import DoctorDashboardPage

@pytest.mark.e2e
class TestE2EIntegration:
    """Complete system-wide E2E verification of the AyurPulse clinical platform."""
    
    @pytest.fixture(autouse=True)
    def setup_credentials(self):
        rand_id = random.randint(10000, 99999)
        self.patient_name = f"E2E Patient {rand_id}"
        self.patient_email = f"e2e_patient_{rand_id}@ayurtest.com"
        
        self.doctor_name = f"Dr. E2E Expert {rand_id}"
        self.doctor_email = f"e2e_doctor_{rand_id}@ayurtest.com"
        
        self.password = "Password@123"
        self.custom_advice = f"E2E Audit Notes: Add turmeric face pack. Drink 3L warm water. ({rand_id})"
        
    def test_ayurpulse_e2e_workflow(self, driver, skin_image):
        """
        Executes a complete end-to-end integration scenario:
        1. Register a Patient
        2. Register an Ayurvedic Doctor
        3. Patient log in, upload face image, complete Prakriti Quiz, and generate plan.
        4. Doctor log in, claim plan from queue, input customized recommendations, and approve.
        5. Patient logs back in, verifies the 'Verified' badge, and verifies doctor notes.
        6. Geolocation search verify.
        """
        # Instantiate page objects
        register_patient_page = RegisterPatientPage(driver)
        register_doctor_page = RegisterDoctorPage(driver)
        login_page = LoginPage(driver)
        patient_dash = PatientDashboardPage(driver)
        doctor_dash = DoctorDashboardPage(driver)
        
        print("\n[E2E] Phase 1: Patient Registration")
        register_patient_page.navigate().register_patient(
            self.patient_name,
            self.patient_email,
            self.password
        )
        register_patient_page.wait_for_url("/login")
        
        print("[E2E] Phase 2: Doctor Registration")
        register_doctor_page.navigate().register_doctor(
            self.doctor_name,
            self.doctor_email,
            self.password,
            specialization="Ayurvedic Dermatology",
            experience_years=18,
            clinic_address="108 Dhanvantari Road, Pune"
        )
        register_doctor_page.wait_for_url("/login")
        
        print("[E2E] Phase 3: Patient Login & Plan Generation")
        login_page.login(self.patient_email, self.password)
        patient_dash.verify_on_dashboard()
        
        # Upload skin image and analyze
        patient_dash.perform_skin_scan(skin_image)
        
        # Answer Prakriti quiz questions
        patient_dash.answer_prakriti_quiz([1, 5, 8, 11, 14, 17])
        
        # Select combinations and generate plan
        patient_dash.configure_profile_and_generate_plan(
            skin_type="combination",
            age_group="21-30",
            season="summer",
            lifestyle_stress=True
        )
        patient_dash.sign_out()
        
        print("[E2E] Phase 4: Doctor Login & Medical Audit Vetting")
        login_page.login(self.doctor_email, self.password)
        doctor_dash.verify_on_dashboard()
        
        # Review pending plans queue, customize, and approve plan
        doctor_dash.review_and_approve_plan(self.custom_advice)
        doctor_dash.sign_out()
        
        print("[E2E] Phase 5: Patient Plan & Notes Verification")
        login_page.login(self.patient_email, self.password)
        patient_dash.verify_on_dashboard()
        
        # Verify approved vetted state and custom medical note injection
        patient_dash.verify_vetted_plan(self.custom_advice)
        
        print("[E2E] Phase 6: Geolocation Pharmacy Geosearch")
        # Validate coordinates search functionality works
        patient_dash.find_nearby_shops(latitude=18.5204, longitude=73.8567)
        patient_dash.sign_out()
        
        print("\n🎉 E2E INTEGRATION FLOW SUCCESSFUL 🎉")
