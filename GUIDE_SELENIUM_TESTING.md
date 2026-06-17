# 🧪 AyurPulse Selenium WebDriver Testing Guide: E2E Quality Assurance

This document serves as the comprehensive source of truth for the **End-to-End Automation Testing** framework of the **AyurPulse** application. It details the Page Object Model (POM) architecture, advanced wait strategies, obscured element handlers, automated screenshot hooks, and includes a standalone script for live-coding exercises.

---

## 🏛️ 1. Test Automation Framework Architecture

The framework is engineered using industry-standard enterprise patterns in Python:
*   **Selenium 4 WebDriver:** Programmatically controls real browser instances via the W3C WebDriver Protocol.
*   **Pytest:** Standard Python test runner managing setup/teardown hooks and test fixtures.
*   **Page Object Model (POM) Pattern:** Encapsulates web page locators and operational behaviors into dedicated Python classes, keeping test scripts clean and maintainable.
*   **WebDriver Manager:** Automatically detects the local Chrome version, downloads the correct ChromeDriver binary, and configures it at runtime, eliminating manual binary management.

```text
automation_tests/
├── pages/                  # Page Object Classes
│   ├── base_page.py        # Reusable browser actions (clicks, types, explicit waits)
│   ├── login_page.py       # Login form handlers
│   ├── register_patient.py # Patient registration page
│   ├── patient_dashboard.py# Image uploads, quiz wizard, coordinates maps search
│   └── doctor_dashboard.py # Specialty queues, scheduler editors, save vetting approvals
├── tests/                  # Pytest Assertions Cases
│   ├── test_auth.py        # Onboarding flows
│   ├── test_patient_flow.py# Diagnostic journeys
│   ├── test_doctor_flow.py # Auditing and custom plan edits
│   └── test_e2e_integration.py # Master E2E integration test case
├── conftest.py             # Setup/Teardown fixtures & screenshot hooks
└── pytest.ini              # Framework runner configurations
```

---

## 🧬 2. Advanced E2E Automation Workflows

The master integration test case (`test_e2e_integration.py`) validates the complete system flow:
1.  **Onboarding:** Automatically generates randomized test credentials, registers a new patient, registers a new doctor (complete with specialization, experience, and clinic address), and verifies successful database creation.
2.  **Diagnostic Journey:** Logs in as the patient, uploads a skin scan image, completes the 6-question Prakriti quiz, and clicks "Generate Plan."
3.  **Medical Audit:** Logs in as the doctor, navigates to the specialization queue, claims the patient's plan, edits recommendation text blocks, signs custom annotations, and clicks "Approve & Save Vetted Plan."
4.  **Verification:** Logs back in as the patient, navigates to their plans, asserts the presence of the **Verified Green Badge**, opens the plan, and asserts that the doctor's custom annotation is present in the DOM.

---

## ⚡ 3. Advanced Selenium Automation Strategies

### 3.1. Dual Waiting Strategy (Explicit Waits Only)
We completely avoided hardcoded sleeps (e.g. `time.sleep(10)`), which slow down execution and cause flaky tests. Instead, we use **Explicit Waits (`WebDriverWait`)** to poll the DOM dynamically until specific conditions are met:
*   **Standard Wait (30s):** Applied to general UI elements (buttons, inputs, links).
*   **ML Diagnostic Wait (120s):** Applied specifically to the AI skin scan result container. This allows the backend to complete image saving, PyTorch model loading, and database writes before the test script asserts the results, ensuring test reliability.

```python
# Technical snapshot from base_page.py
def find_visible_element(self, locator, timeout=30):
    return WebDriverWait(self.driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )
```

### 3.2. Obscured Element Click Handlers
Standard clicks throw `ElementClickInterceptedException` if elements are obscured by loading spinners, tooltips, or modals. We solved this by implementing a JavaScript executor fallback within `BasePage`:
```python
def click(self, locator):
    element = self.find_clickable_element(locator)
    try:
        element.click()
    except Exception:
        # Fallback to direct JavaScript engine execution if intercepted
        self.driver.execute_script("arguments[0].click();", element)
```

### 3.3. Automated Screenshot Capture on Failure
To simplify debugging, we configured a hook in `conftest.py` that listens for test failures, captures a screenshot, and embeds it directly into the HTML test report:
1.  **Makereport Hook:** `pytest_runtest_makereport` intercepts failures.
2.  **Screenshot Generation:** If a test fails, the hook accesses the active WebDriver instance, captures a PNG screenshot, and saves it to `screenshots/` with a timestamp.
3.  **HTML Embedding:** The screenshot is automatically embedded directly next to the failed test details in `reports/report.html`.

---

## 📝 4. Standalone Live-Coding Script

If asked to write a clean, robust, standalone Selenium automation script from scratch in an interview, write this code. It features standard imports, exception safety, and explicit waits:

```python
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. Initialize browser service automatically using WebDriver Manager
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--window-size=1280,1024")
options.add_argument("--headless=new")  # Run silently (remove to see headed mode browser)

driver = webdriver.Chrome(service=service, options=options)

try:
    # 2. Open login page
    driver.get("http://localhost:5173/login")
    driver.maximize_window()
    
    # 3. Instantiate explicit wait (15 seconds)
    wait = WebDriverWait(driver, 15)
    
    # 4. Type username (waits until element is visible and interactable)
    email_field = wait.until(EC.visibility_of_element_located((By.ID, "email")))
    email_field.clear()
    email_field.send_keys("patient_test_account@ayurtest.com")
    
    # 5. Type password
    password_field = wait.until(EC.visibility_of_element_located((By.ID, "password")))
    password_field.clear()
    password_field.send_keys("SecurePassword123!")
    
    # 6. Click submit button
    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    submit_btn.click()
    
    # 7. Assert login success (Wait until dashboard url is loaded)
    wait.until(EC.url_contains("/dashboard"))
    print("Assertion Passed: Redirected to dashboard successfully!")
    
    # 8. Assert user profile loaded in the DOM
    profile_badge = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "profile-name")))
    assert "patient" in profile_badge.text.lower(), "Incorrect profile context!"
    print("Assertion Passed: Correct profile elements matched.")
    
except Exception as e:
    print(f"Test Execution Failure: {e}")
    # Save failure diagnostic screenshot
    driver.save_screenshot("failed_live_test.png")
    
finally:
    # 8. Clean up driver process to prevent memory leaks (Zombie processes)
    driver.quit()
```

---

## 💡 5. Interview Focus: Common Selenium Questions & Answers

#### Q1: What is the difference between Implicit and Explicit waits?
**A:** 
*   **Implicit Wait** sets a global timeout for the entire lifecycle of the WebDriver instance. If an element isn't found immediately, the driver polls the DOM until the timeout expires. However, it only checks for element presence, not specific states (like clickability or visibility), and can mask performance bottlenecks.
*   **Explicit Wait** allows you to configure specific wait conditions for specific elements (e.g. waiting for a button to be clickable before clicking). We use explicit waits exclusively to ensure test reliability and handle the 120-second latency of the AI skin scanning process.

#### Q2: What is the Page Object Model (POM), and why is it used?
**A:** POM is a design pattern where each web page is represented by a dedicated class. Page classes encapsulate page locators (selectors) and operational behaviors (e.g. typing credentials or submitting forms), while test classes contain only assertions. This separation of concerns improves code reusability and maintainability: if the UI changes, we only need to update the selectors in the page class once, rather than across multiple test files.

#### Q3: How do you handle screenshots for failing tests in your framework?
**A:** We use Pytest hooks in `conftest.py` to capture screenshots dynamically. We override the `pytest_runtest_makereport` hook to listen for test failures. When a failure is detected, the hook accesses the active WebDriver instance, captures a full-viewport PNG screenshot, saves it to `screenshots/` with a timestamp, and embeds it directly into the HTML test report (`reports/report.html`) next to the failed test case for fast debugging.

#### Q4: How do you handle elements that are loaded but blocked by overlays?
**A:** Standard clicks throw `ElementClickInterceptedException` if elements are blocked by loading spinners or modals. To handle this reliably, we implemented a fallback click handler in our `BasePage` using a JavaScript executor: if a standard click fails, the driver executes `arguments[0].click()` directly in the browser's JS engine, bypassing physical click limitations.
