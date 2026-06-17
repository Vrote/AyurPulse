import random
import pytest
from pages.register_patient_page import RegisterPatientPage
from pages.register_doctor_page import RegisterDoctorPage
from pages.login_page import LoginPage
from pages.patient_dashboard_page import PatientDashboardPage
from pages.doctor_dashboard_page import DoctorDashboardPage

@pytest.mark.doctor
class TestDoctorFlow:
    """Validates practitioner clinical vetting queue reviews and plan modification approval."""
    
    @pytest.fixture(autouse=True)
    def setup_credentials(self):
        rand_id = random.randint(10000, 99999)
        self.patient_name = f"Audit Patient {rand_id}"
        self.patient_email = f"audit_patient_{rand_id}@ayurtest.com"
        
        self.doctor_name = f"Dr. Dermatologist {rand_id}"
        self.doctor_email = f"audit_doctor_{rand_id}@ayurtest.com"
        
        self.password = "Password@123"
        self.custom_advice = f"Doctor Flow Note: Drink warm herbal tea daily ({rand_id})."
        
    def test_doctor_plan_vetting(self, driver, skin_image):
        """Creates a patient and a pending plan, then logs in as a doctor to audit, modify, and approve the plan."""
        # 1. Register & Login Patient
        RegisterPatientPage(driver).navigate().register_patient(
            self.patient_name, self.patient_email, self.password
        )
        LoginPage(driver).navigate().login(self.patient_email, self.password)
        
        # 2. Upload Scan and Submit Prakriti Quiz to generate plan
        patient_dash = PatientDashboardPage(driver)
        patient_dash.verify_on_dashboard()
        patient_dash.perform_skin_scan(skin_image)
        patient_dash.answer_prakriti_quiz([1, 5, 8, 11, 14, 17])
        patient_dash.configure_profile_and_generate_plan(
            skin_type="combination",
            age_group="21-30",
            season="summer",
            lifestyle_stress=True
        )
        patient_dash.sign_out()
        
        # 3. Register & Login Doctor
        RegisterDoctorPage(driver).navigate().register_doctor(
            self.doctor_name,
            self.doctor_email,
            self.password,
            specialization="Ayurvedic Dermatology",
            experience_years=15,
            clinic_address="789 Dhanvantari Path, Pune"
        )
        LoginPage(driver).navigate().login(self.doctor_email, self.password)
        
        # 4. Access Vetting Queue, inject custom advice, and save vetted plan
        doctor_dash = DoctorDashboardPage(driver)
        doctor_dash.verify_on_dashboard()
        doctor_dash.review_and_approve_plan(self.custom_advice)
        doctor_dash.sign_out()
        
        print("[+] Doctor clinical plan auditing workflow completed successfully.")
