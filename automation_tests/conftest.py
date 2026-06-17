import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.helpers import create_dummy_skin_image

def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run tests in headed mode (visible browser). Default is headless."
    )

@pytest.fixture(scope="function")
def driver(request):
    headed = request.config.getoption("--headed")
    options = Options()
    if not headed:
        options.add_argument("--headless=new")
    
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--log-level=3")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Auto driver install & startup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    
    yield driver
    
    driver.quit()

@pytest.fixture(scope="session")
def skin_image():
    """Provides path to a valid skin image, and deletes it at the end of session if it was a temporary fallback."""
    img_path = create_dummy_skin_image()
    yield img_path
    if os.path.exists(img_path) and "temp_face.png" in img_path:
        try:
            os.remove(img_path)
            print("[*] Cleaned up temporary dummy skin image.")
        except Exception as e:
            print(f"[-] Failed to clean up temp dummy image: {e}")

# HTML Report Screenshots attachment on test failure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    extra = getattr(rep, "extra", [])
    
    if rep.when == "call" and rep.failed:
        driver_fixture = item.funcargs.get("driver", None)
        if driver_fixture:
            os.makedirs("screenshots", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"{item.name}_{timestamp}.png"
            screenshot_path = os.path.join("screenshots", screenshot_name)
            
            try:
                driver_fixture.save_screenshot(screenshot_path)
                # Since the reports/report.html is inside reports/, the relative path to screenshots is ../screenshots/filename.png
                relative_path = os.path.join("..", "screenshots", screenshot_name)
                
                try:
                    import pytest_html
                    extra.append(pytest_html.extras.image(relative_path))
                except ImportError:
                    pass
            except Exception as e:
                print(f"[-] Failed to capture screenshot on failure: {e}")
                
    rep.extra = extra
