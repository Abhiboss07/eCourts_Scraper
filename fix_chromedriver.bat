@echo off
echo ============================================================
echo ChromeDriver Fix Tool
echo ============================================================
echo.
echo This will:
echo 1. Clear ChromeDriver cache
echo 2. Upgrade Selenium and webdriver-manager
echo 3. Force fresh ChromeDriver download
echo.
echo ============================================================
echo.

python fix_chromedriver.py

echo.
echo ============================================================
echo Done! Now try running: python test_captcha.py
echo ============================================================
echo.
pause
