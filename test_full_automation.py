#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Full Automation - CAPTCHA to Results
This script tests the complete automation flow
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import ECourtsScraper
import json
import time

def test_full_automation():
    """Test complete automation from CAPTCHA to results"""
    
    print("="*70)
    print("🤖 TESTING FULL AUTOMATION")
    print("="*70)
    print()
    print("This test will:")
    print("1. ✅ Open browser")
    print("2. ✅ Load eCourts website")
    print("3. ✅ Enter CNR automatically")
    print("4. ✅ Detect CAPTCHA")
    print("5. ✅ Take screenshot")
    print("6. ✅ Extract text using OCR")
    print("7. ✅ Fill CAPTCHA automatically")
    print("8. ✅ Click search button automatically")
    print("9. ✅ Parse results")
    print("10. ✅ Display in terminal")
    print()
    print("="*70)
    print()
    
    # Get CNR from user
    test_cnr = input("Enter CNR to test (or press Enter for example): ").strip()
    
    if not test_cnr:
        test_cnr = "MHAU019999992015"
        print(f"Using example CNR: {test_cnr}")
    
    print()
    print("🚀 Starting full automation test...")
    print()
    print("⚠️  IMPORTANT: Make sure Tesseract OCR is installed!")
    print("   If not installed, run: install_all.bat")
    print()
    
    # Initialize scraper with auto-CAPTCHA enabled
    print("🔧 Initializing scraper with automatic CAPTCHA solving...")
    scraper = ECourtsScraper(headless=False, auto_captcha=True)
    
    try:
        print()
        print("="*70)
        print("🎬 AUTOMATION STARTED")
        print("="*70)
        print()
        
        start_time = time.time()
        
        # Search - Everything happens automatically!
        result = scraper.search_by_cnr(test_cnr)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print()
        print("="*70)
        print("📊 AUTOMATION RESULTS")
        print("="*70)
        print()
        
        if result:
            print("✅ SUCCESS! Full automation completed!")
            print(f"⏱️  Total time: {elapsed:.2f} seconds")
            print()
            print("="*70)
            print("📋 CASE DETAILS (Terminal Output)")
            print("="*70)
            print()
            
            # Display in terminal (formatted)
            for key, value in result.items():
                print(f"  {key.upper():20s}: {value}")
            
            print()
            print("="*70)
            print("💾 SAVING RESULTS")
            print("="*70)
            print()
            
            # Save as JSON
            filename = f"outputs/case_{test_cnr}_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            print(f"✅ JSON saved: {filename}")
            
            # Save as text
            txt_filename = filename.replace('.json', '.txt')
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("ECOURTS CASE DETAILS\n")
                f.write("="*70 + "\n\n")
                for key, value in result.items():
                    f.write(f"{key.upper():20s}: {value}\n")
                f.write("\n" + "="*70 + "\n")
            print(f"✅ Text saved: {txt_filename}")
            
            print()
            print("="*70)
            print("🎉 FULL AUTOMATION TEST PASSED!")
            print("="*70)
            print()
            print("Summary:")
            print(f"  ✅ CAPTCHA solved automatically")
            print(f"  ✅ Search clicked automatically")
            print(f"  ✅ Results parsed successfully")
            print(f"  ✅ Data displayed in terminal")
            print(f"  ✅ Files saved to outputs/")
            print(f"  ⏱️  Total time: {elapsed:.2f} seconds")
            print()
            
        else:
            print("❌ AUTOMATION FAILED")
            print()
            print("Possible reasons:")
            print("  1. Tesseract OCR not installed")
            print("  2. CAPTCHA text extraction failed")
            print("  3. CNR number invalid")
            print("  4. Network timeout")
            print("  5. eCourts website structure changed")
            print()
            print("Solutions:")
            print("  1. Install Tesseract: See INSTALL_TESSERACT.md")
            print("  2. Check captcha_images/ folder for screenshots")
            print("  3. Try a different CNR")
            print("  4. Check internet connection")
            print("  5. Update element selectors in scraper.py")
            print()
        
        print("="*70)
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ ERROR DURING AUTOMATION")
        print("="*70)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        print()
        print("Please check:")
        print("  1. Tesseract is installed (tesseract --version)")
        print("  2. All packages installed (pip install -r requirements.txt)")
        print("  3. Chrome browser is installed")
        print("  4. Internet connection is working")
        print()
    
    finally:
        # Close browser
        print()
        print("🔒 Closing browser...")
        scraper.close()
        print("✅ Browser closed")
        print()
        print("="*70)
        print("Test completed!")
        print("="*70)


def test_web_interface_integration():
    """Show how results are sent to web interface"""
    
    print()
    print("="*70)
    print("🌐 WEB INTERFACE INTEGRATION")
    print("="*70)
    print()
    print("When using the web interface (http://localhost:5000):")
    print()
    print("1. User enters CNR in web form")
    print("2. AJAX request sent to /api/search/cnr")
    print("3. Backend (app.py) calls scraper.search_by_cnr()")
    print("4. Scraper automatically:")
    print("   - Detects CAPTCHA")
    print("   - Takes screenshot")
    print("   - Extracts text with OCR")
    print("   - Fills CAPTCHA")
    print("   - Clicks search")
    print("   - Parses results")
    print("5. Results returned as JSON to frontend")
    print("6. Frontend displays results in browser")
    print()
    print("All automatic! No manual intervention needed!")
    print()
    print("="*70)


if __name__ == "__main__":
    # Test full automation
    test_full_automation()
    
    # Show web integration info
    test_web_interface_integration()
    
    print()
    print("🎉 To use with web interface:")
    print("   1. Run: python app.py")
    print("   2. Open: http://localhost:5000")
    print("   3. Enter CNR and click Search")
    print("   4. Results appear automatically!")
    print()
