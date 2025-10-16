@echo off
echo ============================================================
echo eCourts Scraper - Automatic CAPTCHA Mode
echo ============================================================
echo.
echo This will:
echo 1. Verify Tesseract is installed
echo 2. Run full automation test
echo 3. Solve CAPTCHA automatically
echo 4. Display results
echo.
echo ============================================================
echo.

echo Step 1: Verifying Tesseract installation...
echo.
python verify_tesseract.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Tesseract verification failed!
    echo.
    echo Please install Tesseract from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2: Running full automation test...
echo ============================================================
echo.

python test_full_automation.py

echo.
echo ============================================================
echo Test completed!
echo ============================================================
echo.
pause
