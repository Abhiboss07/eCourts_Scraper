#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Test - Works with or without Tesseract
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import ECourtsScraper
import time

print("="*70)
print("🧪 SIMPLE TEST - Manual CAPTCHA Mode")
print("="*70)
print()
print("This test will:")
print("1. Open browser (you'll see it)")
print("2. Load eCourts website")
print("3. Enter CNR")
print("4. Show CAPTCHA")
print("5. YOU solve the CAPTCHA manually")
print("6. Script clicks search automatically")
print("7. Results displayed")
print()
print("="*70)
print()

# Get CNR
cnr = input("Enter CNR (or press Enter for example): ").strip()
if not cnr:
    cnr = "DLHC010123452023"
    print(f"Using example: {cnr}")

print()
print("🚀 Starting test...")
print()

# Initialize WITHOUT auto-captcha (manual mode)
print("📝 Note: Auto-CAPTCHA is disabled for this test")
print("   You will solve CAPTCHA manually")
print()

scraper = ECourtsScraper(headless=False, auto_captcha=False)

try:
    print("🔍 Searching...")
    print()
    
    result = scraper.search_by_cnr(cnr)
    
    print()
    print("="*70)
    if result:
        print("✅ SUCCESS!")
        print("="*70)
        print()
        print("📋 CASE DETAILS:")
        print()
        for key, value in result.items():
            print(f"  {key:20s}: {value}")
        print()
        print("="*70)
        print("✅ Test PASSED!")
        print("="*70)
    else:
        print("❌ FAILED - No results")
        print("="*70)
        print()
        print("Possible reasons:")
        print("1. CAPTCHA was not solved correctly")
        print("2. CNR number is invalid")
        print("3. Case doesn't exist")
        print()
        print("Try again with:")
        print("  python test_simple.py")
        print()
        
except Exception as e:
    print()
    print("="*70)
    print("❌ ERROR")
    print("="*70)
    print(f"\n{e}\n")
    import traceback
    traceback.print_exc()
    
finally:
    print()
    print("🔒 Closing browser...")
    scraper.close()
    print("✅ Done!")
    print()
