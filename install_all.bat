@echo off
echo ============================================================
echo eCourts Scraper - Complete Installation
echo ============================================================
echo.
echo This will install:
echo 1. Python packages (Flask, Selenium, etc.)
echo 2. OCR packages (pytesseract, Pillow, opencv-python)
echo 3. Check for Tesseract OCR
echo.
echo ============================================================
echo.

echo Step 1: Installing Python packages...
echo.
pip install -r requirements.txt

echo.
echo ============================================================
echo Step 2: Checking Tesseract OCR installation...
echo.

tesseract --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Tesseract is already installed!
    tesseract --version
) else (
    echo ❌ Tesseract is NOT installed
    echo.
    echo Please install Tesseract OCR manually:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Run the installer
    echo 3. Install to: C:\Program Files\Tesseract-OCR
    echo 4. Add to PATH when prompted
    echo.
    echo After installation, run this script again.
    echo.
    echo Opening download page in browser...
    start https://github.com/UB-Mannheim/tesseract/wiki
)

echo.
echo ============================================================
echo Step 3: Testing installation...
echo.

python -c "import flask; print('✅ Flask installed')" 2>nul || echo ❌ Flask not installed
python -c "import selenium; print('✅ Selenium installed')" 2>nul || echo ❌ Selenium not installed
python -c "import pytesseract; print('✅ pytesseract installed')" 2>nul || echo ❌ pytesseract not installed
python -c "import PIL; print('✅ Pillow installed')" 2>nul || echo ❌ Pillow not installed
python -c "import cv2; print('✅ OpenCV installed')" 2>nul || echo ❌ OpenCV not installed

echo.
echo ============================================================
echo Installation Summary
echo ============================================================
echo.
echo Python packages: Installed
echo Tesseract OCR: Check above
echo.
echo Next steps:
echo 1. If Tesseract not installed, install it from the opened webpage
echo 2. Run: python test_captcha.py
echo 3. Or run: python app.py
echo.
echo ============================================================
echo.
pause
