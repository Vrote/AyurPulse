# AyurPulse Selenium WebDriver Automation Framework

This directory houses a clean, maintainable, scalable, industry-standard **Selenium WebDriver End-to-End Automation Framework** built using Python, `pytest`, and the **Page Object Model (POM)** pattern.

The test suite is structured around the actual functional modules and pages present in the AyurPulse clinical platform.

---

## 📂 Framework Directory Structure

```text
automation_tests/
├── pages/
│   ├── base_page.py              # Reusable wrapper operations (wait helpers, clicks, types)
│   ├── login_page.py             # User & Doctor Login page actions
│   ├── register_patient_page.py  # Patient Registration inputs
│   ├── register_doctor_page.py   # Doctor Registration inputs (specialization, experience, clinic address)
│   ├── patient_dashboard_page.py # Skin scan, Prakriti quiz, plan customization, shops locator
│   └── doctor_dashboard_page.py  # Vetting queue review, expert notes, clinical vetting approvals
│
├── tests/
│   ├── test_auth.py              # Tests covering Patient and Doctor registrations/logins
│   ├── test_patient_flow.py      # Skin diagnostic scan, quiz submission, personalization, shops locator search
│   ├── test_doctor_flow.py       # Doctor's vetting queue audits and approvals
│   └── test_e2e_integration.py   # Complete integrated Patient -> Doctor -> Patient vetted E2E verification
│
├── utils/
│   └── helpers.py                # Pillow fallback image generator & explicit wait wrappers
│
├── test_data/
│   └── test_constants.py         # Static configuration, page URLs, credentials, coordinate targets
│
├── reports/                      # Output directory for pytest-html test execution reports
├── screenshots/                  # Output directory for test failure screenshots (auto-captured with timestamps)
│
├── conftest.py                   # Pytest runner configurations, driver setups, failure hooks
├── pytest.ini                    # Pytest framework settings
└── README.md                     # This file
```

---

## 🛠️ Installation & Dependency Setup

### 1. Set Up Python Environment
Ensure you have Python 3.8+ installed on your system. It is highly recommended to run tests in the same virtual environment configured for the AyurPulse backend, or set up a clean dedicated environment:

```powershell
# Navigate to the automation_tests folder
cd automation_tests

# Install all framework requirements
..\Ayurpulse\venv\Scripts\pip install -r requirements.txt
```

### 2. Verify External Services
Ensure that both your frontend and backend servers are up and active:
- **FastAPI Backend**: Running at `http://127.0.0.1:8000`
- **React Frontend**: Running at `http://localhost:5173`

---

## 🧪 Test Execution

Tests are launched using `pytest`. By default, execution runs in **headless (silent) mode**.

### 1. Run All Tests (Headless Mode)
To run the complete test suite in headless mode:
```powershell
pytest
```

### 2. Run All Tests (Headed / Visible Browser Mode)
To see the browser interact with the UI elements in real-time, pass the `--headed` flag:
```powershell
pytest --headed
```

### 3. Run Specific Test Suites
You can run specific test suites by targeting their files:
```powershell
# Run Authentication tests
pytest tests/test_auth.py -v

# Run Patient Flow tests
pytest tests/test_patient_flow.py -v

# Run Doctor Auditing tests
pytest tests/test_doctor_flow.py -v

# Run E2E Integration flows
pytest tests/test_e2e_integration.py -v
```

---

## 📊 Reports & Failure Handling

### 1. HTML Execution Reports
A self-contained HTML report is automatically compiled on every test run using `pytest-html`.
The report is saved to:
`automation_tests/reports/report.html`

### 2. Screenshot Capture on Failure
If any test assertion or wait timeout fails during execution:
- A browser screenshot is automatically captured.
- Saved in the `automation_tests/screenshots/` directory with a timestamp.
- **Embedded Directly**: The screenshot is automatically embedded inside the interactive HTML execution report next to the failing test case details for convenient debugging.

---

## ⚙️ Automation Design Standards & Best Practices

1. **Page Object Model (POM)**: High cohesion and loose coupling. All locators and operational behaviors are encapsulated strictly within page classes under `/pages`.
2. **Explicit Waits Only**: The framework uses `WebDriverWait` paired with `expected_conditions` exclusively (wrapped under `ElementWait` and `BasePage`). The code is entirely free of hardcoded `time.sleep()`, ensuring maximum execution speed and high stability.
3. **Automatic Driver Management**: No need to manually download or link browser binaries. `webdriver-manager` automatically manages, updates, and sets up correct Chrome browser versions dynamically.
