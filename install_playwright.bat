@echo off
echo ============================================================
echo INSTALLING PLAYWRIGHT FOR ECOURTS SCRAPER
echo ============================================================
echo.

echo Step 1: Uninstalling Selenium (optional)...
pip uninstall -y selenium webdriver-manager
echo.

echo Step 2: Installing Playwright and dependencies...
pip install -r requirements_playwright.txt
echo.

echo Step 3: Installing Playwright browsers...
playwright install chromium
echo.

echo ============================================================
echo INSTALLATION COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo 1. Test the scraper: python test_playwright.py
echo 2. Update app.py to use: from scraper_playwright import ECourtsScraper
echo.
pause
