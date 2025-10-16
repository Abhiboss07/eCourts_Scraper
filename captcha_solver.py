#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic CAPTCHA Solver using EasyOCR (No Tesseract needed!)
"""

import os
import time
import re
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# Use EasyOCR instead of Tesseract
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️  EasyOCR not available. Install: pip install easyocr")

class CaptchaSolver:
    """Automatic CAPTCHA solver using EasyOCR (No Tesseract needed!)"""
    
    def __init__(self):
        """Initialize CAPTCHA solver"""
        self.captcha_dir = "captcha_images"
        self._ensure_captcha_dir()
        
        # Initialize EasyOCR reader
        self.reader = None
        if EASYOCR_AVAILABLE:
            try:
                print("🔧 Initializing EasyOCR (first time may download models)...")
                # Initialize with English only for faster performance
                self.reader = easyocr.Reader(['en'], gpu=False)
                print("✅ EasyOCR initialized successfully!")
            except Exception as e:
                print(f"⚠️  EasyOCR initialization failed: {e}")
                self.reader = None
    
    def _ensure_captcha_dir(self):
        """Create directory for CAPTCHA images"""
        if not os.path.exists(self.captcha_dir):
            os.makedirs(self.captcha_dir)
    
    def save_captcha_screenshot(self, driver, captcha_element):
        """
        Take screenshot of CAPTCHA element
        
        Args:
            driver: Selenium WebDriver instance
            captcha_element: CAPTCHA image element
            
        Returns:
            Path to saved screenshot
        """
        try:
            timestamp = int(time.time())
            screenshot_path = os.path.join(self.captcha_dir, f"captcha_{timestamp}.png")
            
            # Take screenshot of the element
            captcha_element.screenshot(screenshot_path)
            print(f"📸 CAPTCHA screenshot saved: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"❌ Error saving CAPTCHA screenshot: {e}")
            
            # Fallback: take full page screenshot
            try:
                screenshot_path = os.path.join(self.captcha_dir, f"captcha_full_{timestamp}.png")
                driver.save_screenshot(screenshot_path)
                print(f"📸 Full page screenshot saved: {screenshot_path}")
                return screenshot_path
            except:
                return None
    
    def preprocess_image(self, image_path):
        """
        Preprocess CAPTCHA image for better OCR accuracy
        
        Args:
            image_path: Path to CAPTCHA image
            
        Returns:
            Preprocessed image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            
            if img is None:
                print("❌ Could not read image")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to get black and white image
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # Remove noise
            denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
            
            # Invert back
            inverted = cv2.bitwise_not(denoised)
            
            # Increase contrast
            pil_img = Image.fromarray(inverted)
            enhancer = ImageEnhance.Contrast(pil_img)
            enhanced = enhancer.enhance(2.0)
            
            # Sharpen
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            
            # Save preprocessed image
            processed_path = image_path.replace('.png', '_processed.png')
            sharpened.save(processed_path)
            print(f"✅ Preprocessed image saved: {processed_path}")
            
            return processed_path
            
        except Exception as e:
            print(f"⚠️  Preprocessing failed: {e}")
            return image_path  # Return original if preprocessing fails
    
    def extract_text_from_image(self, image_path):
        """
        Extract text from CAPTCHA image using EasyOCR
        
        Args:
            image_path: Path to CAPTCHA image
            
        Returns:
            Extracted text (cleaned)
        """
        try:
            print(f"🔍 Extracting text from: {image_path}")
            
            if not self.reader:
                print("❌ EasyOCR reader not initialized")
                return None
            
            # Preprocess image
            processed_path = self.preprocess_image(image_path)
            
            if not processed_path:
                processed_path = image_path
            
            # Try with original image
            print("   Trying original image...")
            result_original = self.reader.readtext(image_path, detail=1)
            
            # Try with preprocessed image
            print("   Trying preprocessed image...")
            result_processed = self.reader.readtext(processed_path, detail=1)
            
            # Combine results and pick best
            all_results = result_original + result_processed
            
            if not all_results:
                print("❌ Could not extract text from CAPTCHA")
                return None
            
            # Sort by confidence and get best result
            all_results.sort(key=lambda x: x[2], reverse=True)
            
            best_texts = []
            for bbox, text, confidence in all_results[:3]:  # Top 3 results
                cleaned = self._clean_text(text)
                if cleaned:
                    print(f"   Confidence {confidence:.2f} → '{cleaned}'")
                    best_texts.append((cleaned, confidence))
            
            if best_texts:
                # Return the one with highest confidence
                best_text = best_texts[0][0]
                print(f"✅ Extracted CAPTCHA text: '{best_text}'")
                return best_text
            else:
                print("❌ Could not extract valid text from CAPTCHA")
                return None
                
        except Exception as e:
            print(f"❌ OCR error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _clean_text(self, text):
        """
        Clean extracted text
        
        Args:
            text: Raw OCR output
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove whitespace
        cleaned = text.strip()
        
        # Remove special characters
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', cleaned)
        
        # Common OCR corrections
        corrections = {
            'O': '0',  # Letter O to zero
            'l': '1',  # Lowercase L to one
            'I': '1',  # Uppercase i to one
            'S': '5',  # Sometimes S looks like 5
            'Z': '2',  # Sometimes Z looks like 2
        }
        
        # Apply corrections (optional, might not always be correct)
        # Uncomment if needed:
        # for old, new in corrections.items():
        #     cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    def solve_captcha(self, driver, captcha_element, captcha_input_element):
        """
        Automatically solve CAPTCHA
        
        Args:
            driver: Selenium WebDriver
            captcha_element: CAPTCHA image element
            captcha_input_element: CAPTCHA input field element
            
        Returns:
            True if solved successfully, False otherwise
        """
        try:
            print("\n" + "="*60)
            print("🤖 AUTOMATIC CAPTCHA SOLVING")
            print("="*60)
            
            # Step 1: Take screenshot
            print("\n📸 Step 1: Taking CAPTCHA screenshot...")
            screenshot_path = self.save_captcha_screenshot(driver, captcha_element)
            
            if not screenshot_path:
                print("❌ Failed to capture CAPTCHA")
                return False
            
            # Step 2: Extract text using OCR
            print("\n🔍 Step 2: Extracting text using OCR...")
            captcha_text = self.extract_text_from_image(screenshot_path)
            
            if not captcha_text:
                print("❌ Failed to extract CAPTCHA text")
                return False
            
            # Step 3: Fill in CAPTCHA
            print(f"\n✍️  Step 3: Filling CAPTCHA: '{captcha_text}'")
            captcha_input_element.clear()
            captcha_input_element.send_keys(captcha_text)  # No delay needed
            
            print("✅ CAPTCHA filled successfully!")
            print("="*60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Error solving CAPTCHA: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_easyocr_available(self):
        """Check if EasyOCR is available"""
        return self.reader is not None


# Test function
if __name__ == "__main__":
    print("="*70)
    print("🤖 EasyOCR CAPTCHA Solver Test")
    print("="*70)
    print()
    print("No Tesseract installation needed!")
    print("Using pure Python EasyOCR library.")
    print()
    
    solver = CaptchaSolver()
    
    if solver.is_easyocr_available():
        print("✅ EasyOCR is ready!")
        print("✅ CAPTCHA solver is ready to use!")
        print()
        print("You can now run:")
        print("  python test_full_automation.py")
    else:
        print("❌ EasyOCR is NOT available!")
        print()
        print("Please install EasyOCR:")
        print("  pip install easyocr torch torchvision")
        print()
        print("Or install all requirements:")
        print("  pip install -r requirements.txt")
    
    print()
    print("="*70)
