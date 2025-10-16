#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic Script - Find CAPTCHA Input Field
This script helps identify the actual CAPTCHA input field on eCourts website
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

print("="*70)
print("🔍 CAPTCHA INPUT FIELD FINDER")
print("="*70)
print()
print("This script will:")
print("1. Open eCourts website")
print("2. Find all input fields")
print("3. Identify which one is the CAPTCHA input")
print("4. Show you the exact selector to use")
print()
print("="*70)
print()

# Initialize browser
print("🔧 Initializing browser...")
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
except:
    driver = webdriver.Chrome(options=chrome_options)

print("✅ Browser initialized")
print()

try:
    # Navigate to eCourts
    print("📡 Loading eCourts website...")
    url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=home/index"
    driver.get(url)
    time.sleep(5)
    print("✅ Page loaded")
    print()
    
    # Enter CNR to trigger CAPTCHA
    print("✍️  Entering CNR to trigger CAPTCHA...")
    cnr_selectors = [
        (By.ID, "cnr_number"),
        (By.NAME, "cnr_number"),
        (By.CSS_SELECTOR, "input[placeholder*='CNR']"),
    ]
    
    cnr_input = None
    for sel_type, sel_value in cnr_selectors:
        try:
            cnr_input = driver.find_element(sel_type, sel_value)
            if cnr_input:
                print(f"✅ Found CNR input")
                break
        except:
            continue
    
    if cnr_input:
        cnr_input.clear()
        cnr_input.send_keys("MHAU019999992015")
        time.sleep(3)
        print("✅ CNR entered, CAPTCHA should be visible now")
    else:
        print("⚠️  Could not find CNR input, but continuing...")
    
    print()
    print("="*70)
    print("🔍 ANALYZING ALL INPUT FIELDS")
    print("="*70)
    print()
    
    # Find all input fields
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    
    print(f"Found {len(all_inputs)} input fields on the page")
    print()
    
    captcha_candidates = []
    
    for idx, input_elem in enumerate(all_inputs):
        try:
            # Get attributes
            input_id = input_elem.get_attribute("id") or ""
            input_name = input_elem.get_attribute("name") or ""
            input_type = input_elem.get_attribute("type") or ""
            input_placeholder = input_elem.get_attribute("placeholder") or ""
            input_class = input_elem.get_attribute("class") or ""
            input_maxlength = input_elem.get_attribute("maxlength") or ""
            is_visible = input_elem.is_displayed()
            
            # Check if it might be CAPTCHA input
            is_captcha = False
            reason = []
            
            if "captcha" in input_id.lower():
                is_captcha = True
                reason.append("ID contains 'captcha'")
            
            if "captcha" in input_name.lower():
                is_captcha = True
                reason.append("Name contains 'captcha'")
            
            if "captcha" in input_placeholder.lower() or "code" in input_placeholder.lower():
                is_captcha = True
                reason.append("Placeholder mentions captcha/code")
            
            if input_type == "text" and input_maxlength in ["5", "6", "7", "8"]:
                is_captcha = True
                reason.append(f"Text input with maxlength={input_maxlength}")
            
            if is_captcha and is_visible:
                captcha_candidates.append({
                    'index': idx,
                    'id': input_id,
                    'name': input_name,
                    'type': input_type,
                    'placeholder': input_placeholder,
                    'class': input_class,
                    'maxlength': input_maxlength,
                    'reason': reason
                })
        
        except Exception as e:
            continue
    
    print("="*70)
    print("🎯 CAPTCHA INPUT CANDIDATES")
    print("="*70)
    print()
    
    if captcha_candidates:
        print(f"Found {len(captcha_candidates)} potential CAPTCHA input field(s):")
        print()
        
        for candidate in captcha_candidates:
            print(f"Candidate #{candidate['index'] + 1}:")
            print(f"  ID:          {candidate['id']}")
            print(f"  Name:        {candidate['name']}")
            print(f"  Type:        {candidate['type']}")
            print(f"  Placeholder: {candidate['placeholder']}")
            print(f"  Class:       {candidate['class']}")
            print(f"  MaxLength:   {candidate['maxlength']}")
            print(f"  Reason:      {', '.join(candidate['reason'])}")
            print()
            
            # Suggest selectors
            print("  📝 Suggested Selectors:")
            if candidate['id']:
                print(f"     By.ID: '{candidate['id']}'")
            if candidate['name']:
                print(f"     By.NAME: '{candidate['name']}'")
            if candidate['id']:
                print(f"     By.CSS_SELECTOR: \"input[id='{candidate['id']}']\"")
            if candidate['name']:
                print(f"     By.CSS_SELECTOR: \"input[name='{candidate['name']}']\"")
            print()
            print("-" * 70)
            print()
        
        # Highlight the most likely one
        best_candidate = captcha_candidates[0]
        print("="*70)
        print("✅ MOST LIKELY CAPTCHA INPUT:")
        print("="*70)
        print()
        print(f"ID:   {best_candidate['id']}")
        print(f"Name: {best_candidate['name']}")
        print()
        print("🔧 ADD THIS TO scraper.py:")
        print()
        if best_candidate['id']:
            print(f"    (By.ID, \"{best_candidate['id']}\"),")
        if best_candidate['name']:
            print(f"    (By.NAME, \"{best_candidate['name']}\"),")
        print()
        
    else:
        print("❌ No obvious CAPTCHA input field found!")
        print()
        print("Showing ALL text input fields:")
        print()
        
        text_inputs = []
        for idx, input_elem in enumerate(all_inputs):
            try:
                input_type = input_elem.get_attribute("type") or ""
                if input_type == "text" and input_elem.is_displayed():
                    input_id = input_elem.get_attribute("id") or ""
                    input_name = input_elem.get_attribute("name") or ""
                    input_placeholder = input_elem.get_attribute("placeholder") or ""
                    
                    print(f"  Input #{idx + 1}:")
                    print(f"    ID: {input_id}")
                    print(f"    Name: {input_name}")
                    print(f"    Placeholder: {input_placeholder}")
                    print()
            except:
                continue
    
    print("="*70)
    print("📸 Taking screenshot for reference...")
    driver.save_screenshot("captcha_input_debug.png")
    print("✅ Screenshot saved: captcha_input_debug.png")
    print()
    
    print("="*70)
    print("⏸️  Browser will stay open for 30 seconds")
    print("   You can inspect the page manually")
    print("="*70)
    time.sleep(30)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print()
    print("🔒 Closing browser...")
    driver.quit()
    print("✅ Done!")
    print()
    print("="*70)
    print("Next steps:")
    print("1. Check the output above for CAPTCHA input field")
    print("2. Look at captcha_input_debug.png screenshot")
    print("3. Update scraper.py with the correct selector")
    print("="*70)
