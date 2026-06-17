import random
import pytest
from pages.register_patient_page import RegisterPatientPage
from pages.register_doctor_page import RegisterDoctorPage
from pages.login_page import LoginPage
from pages.patient_dashboard_page import PatientDashboardPage
from pages.doctor_dashboard_page import DoctorDashboardPage

@pytest.mark.auth
class TestAuth:
    """Authentication and Registration tests for Patients and Doctors."""
    
    @pytest.fixture(autouse=True)
    def setup_credentials(self):
        rand_id = random.randint(10000, 99999)
        self.patient_name = f"Auth Patient {rand_id}"
        self.patient_email = f"auth_patient_{rand_id}@ayurtest.com"
        
        self.doctor_name = f"Auth Doctor {rand_id}"
        self.doctor_email = f"auth_doctor_{rand_id}@ayurtest.com"
        
        self.password = "Password@123"
        
    def test_patient_registration_and_login(self, driver):
        """Verify new patients can register and subsequently login to the dashboard."""
        register_page = RegisterPatientPage(driver)
        login_page = LoginPage(driver)
        dashboard_page = PatientDashboardPage(driver)
        
        # 1. Register Patient
        register_page.navigate().register_patient(
            self.patient_name,
            self.patient_email,
            self.password
        )
        
        # Verify redirect to login page
        register_page.wait_for_url("/login")
        
        # 2. Login Patient
        login_page.login(self.patient_email, self.password)
        
        # Verify landing on patient dashboard
        dashboard_page.wait_for_url("/dashboard")
        dashboard_page.verify_on_dashboard()
        
    def test_doctor_registration_and_login(self, driver):
        """Verify new doctors can register with professional details and login to their workspace."""
        register_page = RegisterDoctorPage(driver)
        login_page = LoginPage(driver)
        dashboard_page = DoctorDashboardPage(driver)
        
        # 1. Register Doctor
        register_page.navigate().register_doctor(
            self.doctor_name,
            self.doctor_email,
            self.password,
            specialization="Ayurvedic Dermatology",
            experience_years=10,
            clinic_address="123 Sushruta Marg, Pune"
        )
        
        # Verify redirect to login page
        register_page.wait_for_url("/login")
        
        # 2. Login Doctor
        login_page.login(self.doctor_email, self.password)
        
        # Verify landing on doctor dashboard
        dashboard_page.wait_for_url("/dashboard")
        dashboard_page.verify_on_dashboard()
