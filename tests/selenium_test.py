"""
Selenium WebDriver test for the Library Book Manager.

Usage (from your laptop, after `pip install -r requirements.txt`):
    python selenium_test.py http://<your-ALB-DNS-name>
    python selenium_test.py http://<your-ALB-DNS-name> --headless

What it checks:
  1. The page opens and the browser title is "Library Book Manager"
  2. The <h1 id="app-title"> web element is visible with the right text
  3. A new book can be added through the form and appears in the table
  4. Reloading several times shows which EC2 instance answered each time
     (proves the Load Balancer is spreading traffic across instances)
"""
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = next((a for a in sys.argv[1:] if a.startswith("http")),
           os.getenv("APP_URL", "http://localhost"))
HEADLESS = "--headless" in sys.argv
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SHOTS, exist_ok=True)

passed, failed = 0, 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


def make_driver():
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if os.getenv("CHROME_BIN"):                 # optional custom Chrome path
        opts.binary_location = os.getenv("CHROME_BIN")
    # Selenium 4.6+ downloads the matching chromedriver automatically
    # (Selenium Manager), so no manual driver install is needed.
    return webdriver.Chrome(options=opts)


def main():
    print(f"\nSelenium test -> {URL}\n" + "-" * 60)
    driver = make_driver()
    wait = WebDriverWait(driver, 15)
    try:
        # ---- Test 1: open the application ---------------------------------
        driver.get(URL)
        wait.until(EC.presence_of_element_located((By.ID, "app-title")))
        check("Page title is 'Library Book Manager'",
              driver.title == "Library Book Manager")

        # ---- Test 2: verify a web element --------------------------------
        heading = driver.find_element(By.ID, "app-title")
        check("Heading element is displayed", heading.is_displayed())
        check("Heading text is correct", heading.text == "Library Book Manager")
        check("Add-book form exists", len(driver.find_elements(By.ID, "add-form")) == 1)
        driver.save_screenshot(os.path.join(SHOTS, "01_home_page.png"))

        # ---- Test 3: add a book and verify it is shown --------------------
        new_title = f"Selenium Test Book {int(time.time())}"
        driver.find_element(By.ID, "title").send_keys(new_title)
        driver.find_element(By.ID, "author").send_keys("Selenium WebDriver")
        driver.find_element(By.ID, "add-btn").click()
        wait.until(EC.presence_of_element_located((By.ID, "books-table")))
        titles = [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".book-title")]
        # With 2 instances each has its OWN database, so the redirect may land
        # on the other instance. Reload a few times to find the new book.
        tries = 0
        while new_title not in titles and tries < 6:
            driver.refresh()
            titles = [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".book-title")]
            tries += 1
        check(f"New book '{new_title}' appears in the table", new_title in titles)
        driver.save_screenshot(os.path.join(SHOTS, "02_book_added.png"))

        # ---- Test 4: which instance served each request? ------------------
        seen = []
        for _ in range(6):
            driver.refresh()
            seen.append(driver.find_element(By.ID, "instance-id").text)
        print(f"  [INFO] Instances that answered 6 reloads: {seen}")
        print(f"  [INFO] Distinct instances: {sorted(set(seen))}")
        check("Instance-id element is shown", all(seen))
    finally:
        driver.quit()

    print("-" * 60)
    print(f"RESULT: {passed} passed, {failed} failed")
    print(f"Screenshots saved in: {SHOTS}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
