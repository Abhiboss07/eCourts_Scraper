#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix ChromeDriver installation issues
"""

import os
import shutil
import sys

def fix_chromedriver():
    """Clear ChromeDriver cache and reinstall"""
    
    print("="*70)
    print("🔧 ChromeDriver Fix Tool")
    print("="*70)
    print()
    
    # Find and clear webdriver-manager cache
    cache_dirs = [
        os.path.expanduser("~/.wdm"),
        os.path.expanduser("~/AppData/Local/.wdm"),
        os.path.expanduser("~/AppData/Roaming/.wdm"),
    ]
    
    print("🗑️  Clearing ChromeDriver cache...")
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Cleared: {cache_dir}")
            except Exception as e:
                print(f"   ⚠️  Could not clear {cache_dir}: {e}")
        else:
            print(f"   ℹ️  Not found: {cache_dir}")
    
    print()
    print("📦 Upgrading packages...")
    
    # Upgrade packages
    packages = [
        "selenium",
        "webdriver-manager"
    ]
    
    for package in packages:
        print(f"   Upgrading {package}...")
        os.system(f"pip install --upgrade {package}")
    
    print()
    print("="*70)
    print("✅ Fix completed!")
    print("="*70)
    print()
    print("Now try running:")
    print("   python test_captcha.py")
    print()


if __name__ == "__main__":
    fix_chromedriver()
