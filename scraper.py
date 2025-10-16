#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real eCourts Web Scraper - No Mock Data
Scrapes actual data from https://services.ecourts.gov.in/ecourtindia_v6/
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

# Import CAPTCHA solver
try:
    from captcha_solver import CaptchaSolver
    CAPTCHA_SOLVER_AVAILABLE = True
except ImportError:
    CAPTCHA_SOLVER_AVAILABLE = False
    print("⚠️  CAPTCHA solver not available. Install: pip install pytesseract Pillow opencv-python")


class ECourtsScraper:
    """Real web scraper for eCourts India website"""
    
    BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"
    CNR_SEARCH_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=home/index"
    CASE_STATUS_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/index"
    
    def __init__(self, headless: bool = False, auto_captcha: bool = True):
        """
        Initialize the scraper with Selenium
        
        Args:
            headless: Run browser in headless mode
            auto_captcha: Automatically solve CAPTCHA using OCR
        """
        self.headless = headless
        self.auto_captcha = auto_captcha
        self.driver = None
        self.captcha_solver = None
        
        # Initialize CAPTCHA solver if available and enabled
        if auto_captcha and CAPTCHA_SOLVER_AVAILABLE:
            self.captcha_solver = CaptchaSolver()
            if self.captcha_solver.is_easyocr_available():
                print("✅ Automatic CAPTCHA solving enabled (EasyOCR)")
            else:
                print("⚠️  EasyOCR not available - CAPTCHA solving disabled")
                self.captcha_solver = None
        
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        try:
            print("🔧 Initializing Chrome browser...")
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            # Speed optimizations
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-images')  # Don't load images except CAPTCHA
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            chrome_options.page_load_strategy = 'eager'  # Don't wait for full page load
            
            # Try to use ChromeDriverManager with cache clearing
            try:
                print("📥 Downloading/updating ChromeDriver...")
                from webdriver_manager.chrome import ChromeDriverManager
                from webdriver_manager.core.os_manager import ChromeType
                
                # Clear cache and reinstall
                driver_path = ChromeDriverManager().install()
                print(f"✅ ChromeDriver installed at: {driver_path}")
                
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
            except Exception as e1:
                print(f"⚠️  ChromeDriverManager failed: {e1}")
                print("🔄 Trying alternative method...")
                
                # Try without service (let Selenium find Chrome automatically)
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    print("✅ Using system ChromeDriver")
                except Exception as e2:
                    print(f"❌ Alternative method failed: {e2}")
                    raise Exception(
                        "Failed to initialize Chrome browser.\n"
                        "Please ensure:\n"
                        "1. Google Chrome is installed\n"
                        "2. Chrome version matches ChromeDriver\n"
                        "3. Try running: pip install --upgrade selenium webdriver-manager\n"
                        f"Original error: {e1}"
                    )
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Browser initialized successfully!")
            
        except Exception as e:
            raise Exception(f"Failed to initialize browser: {e}")
    
    def search_by_cnr(self, cnr: str) -> Optional[Dict]:
        """
        Search case by CNR number
        
        Args:
            cnr: 16-digit CNR number
            
        Returns:
            Dictionary with case details or None
        """
        try:
            print(f"🔍 Searching for CNR: {cnr}")
            
            # Navigate to CNR search page
            print("📡 Loading eCourts website...")
            self.driver.get(self.CNR_SEARCH_URL)
            
            # Wait only for essential elements
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("✅ Page loaded")
            except:
                print("⚠️  Page load timeout")
            
            # Find CNR input field with multiple attempts
            cnr_input = None
            print("🔍 Looking for CNR input field...")
            
            # Try multiple selectors
            selectors = [
                (By.ID, "cnr_number"),
                (By.NAME, "cnr_number"),
                (By.CSS_SELECTOR, "input[placeholder*='CNR']"),
                (By.CSS_SELECTOR, "input[name='cnr_number']"),
                (By.XPATH, "//input[@id='cnr_number']"),
                (By.XPATH, "//input[contains(@placeholder, 'CNR')]"),
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    cnr_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    if cnr_input:
                        print(f"✅ Found CNR input using {selector_type}")
                        break
                except:
                    continue
            
            if not cnr_input:
                print("❌ Could not find CNR input field")
                print("📸 Taking screenshot for debugging...")
                self.driver.save_screenshot("debug_cnr_page.png")
                return None
            
            # Clear and enter CNR
            print(f"✍️  Entering CNR: {cnr}")
            cnr_input.clear()
            cnr_input.send_keys(cnr)
            
            # Wait for CAPTCHA to load using explicit wait
            print("⏳ Waiting for CAPTCHA...")
            
            # Look for CAPTCHA image
            captcha_found = False
            captcha_selectors = [
                (By.ID, "captcha_image"),
                (By.ID, "captchaImg"),
                (By.CSS_SELECTOR, "img[alt='Captcha']"),
                (By.CSS_SELECTOR, "img[id*='captcha']"),
                (By.XPATH, "//img[contains(@id, 'captcha')]"),
            ]
            
            for selector_type, selector_value in captcha_selectors:
                try:
                    captcha_img = self.driver.find_element(selector_type, selector_value)
                    if captcha_img:
                        captcha_found = True
                        print(f"✅ CAPTCHA found using {selector_type}")
                        break
                except:
                    continue
            
            if captcha_found:
                print("⚠️  CAPTCHA DETECTED!")
                
                # Try automatic CAPTCHA solving first
                if self.captcha_solver and captcha_img:
                    print("🤖 Attempting automatic CAPTCHA solving...")
                    
                    # Find CAPTCHA input field with extensive selectors
                    captcha_input = None
                    input_selectors = [
                        # Common IDs
                        (By.ID, "captcha"),
                        (By.ID, "captcha_code"),
                        (By.ID, "ansCaptcha"),
                        (By.ID, "captchaCode"),
                        (By.ID, "txtCaptcha"),
                        (By.ID, "cap_code"),
                        (By.ID, "security_code"),
                        
                        # Common Names
                        (By.NAME, "captcha"),
                        (By.NAME, "captcha_code"),
                        (By.NAME, "ansCaptcha"),
                        (By.NAME, "cap_code"),
                        
                        # CSS Selectors
                        (By.CSS_SELECTOR, "input[name='captcha']"),
                        (By.CSS_SELECTOR, "input[id*='captcha']"),
                        (By.CSS_SELECTOR, "input[name*='captcha']"),
                        (By.CSS_SELECTOR, "input[placeholder*='captcha' i]"),
                        (By.CSS_SELECTOR, "input[placeholder*='code' i]"),
                        (By.CSS_SELECTOR, "input[type='text'][maxlength='5']"),
                        (By.CSS_SELECTOR, "input[type='text'][maxlength='6']"),
                        
                        # XPath - by ID
                        (By.XPATH, "//input[@id='captcha']"),
                        (By.XPATH, "//input[@id='ansCaptcha']"),
                        (By.XPATH, "//input[contains(@id, 'captcha')]"),
                        
                        # XPath - by placeholder
                        (By.XPATH, "//input[contains(@placeholder, 'Captcha')]"),
                        (By.XPATH, "//input[contains(@placeholder, 'captcha')]"),
                        (By.XPATH, "//input[contains(@placeholder, 'Code')]"),
                        (By.XPATH, "//input[contains(@placeholder, 'code')]"),
                        
                        # XPath - near CAPTCHA image
                        (By.XPATH, "//img[contains(@id, 'captcha')]/following::input[1]"),
                        (By.XPATH, "//img[contains(@alt, 'Captcha')]/following::input[1]"),
                        
                        # XPath - any text input near CAPTCHA
                        (By.XPATH, "//input[@type='text' and string-length(@maxlength) <= 6]"),
                    ]
                    
                    print(f"🔍 Trying {len(input_selectors)} different selectors for CAPTCHA input...")
                    
                    for sel_type, sel_value in input_selectors:
                        try:
                            captcha_input = self.driver.find_element(sel_type, sel_value)
                            if captcha_input and captcha_input.is_displayed():
                                print(f"✅ Found CAPTCHA input using {sel_type}: {sel_value}")
                                break
                        except:
                            continue
                    
                    if captcha_input:
                        # Attempt automatic solving
                        solved = self.captcha_solver.solve_captcha(
                            self.driver, captcha_img, captcha_input
                        )
                        
                        if solved:
                            print("✅ CAPTCHA solved automatically!")
                        else:
                            print("⚠️  Automatic solving failed, falling back to manual")
                            if not self.headless:
                                print("\n⏳ Please solve CAPTCHA manually (30 seconds)...")
                                time.sleep(30)
                            else:
                                return None
                    else:
                        print("❌ Could not find CAPTCHA input field")
                        if not self.headless:
                            print("\n⏳ Please solve CAPTCHA manually (10 seconds)...")
                            time.sleep(10)  # Further reduced
                        else:
                            return None
                
                # Manual solving fallback
                elif not self.headless:
                    print("")
                    print("="*60)
                    print("   🔐 MANUAL ACTION REQUIRED")
                    print("="*60)
                    print("   1. A browser window should be open")
                    print("   2. Look at the CAPTCHA image")
                    print("   3. Type the CAPTCHA text in the input field")
                    print("   4. Waiting 45 seconds for you to solve it...")
                    print("="*60)
                    print("")
                    
                    # Save screenshot
                    self.driver.save_screenshot("captcha_screenshot.png")
                    print("📸 Screenshot saved as 'captcha_screenshot.png'")
                    
                    # Wait for user to solve CAPTCHA
                    time.sleep(15)  # Further reduced
                else:
                    print("⚠️  Running in headless mode - cannot solve CAPTCHA")
                    print("   Please run with headless=False for manual CAPTCHA solving")
                    return None
            else:
                print("ℹ️  No CAPTCHA detected (or already solved)")
            
            # Find and click search button
            print("🔍 Looking for search button...")
            search_btn = None
            
            button_selectors = [
                (By.ID, "search_btn"),
                (By.ID, "searchBtn"),
                (By.NAME, "search"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Search')]"),
                (By.XPATH, "//input[@value='Search']"),
            ]
            
            for selector_type, selector_value in button_selectors:
                try:
                    search_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if search_btn:
                        print(f"✅ Found search button using {selector_type}")
                        break
                except:
                    continue
            
            if not search_btn:
                print("❌ Could not find search button")
                self.driver.save_screenshot("debug_no_button.png")
                return None
            
            # Click search
            print("🔘 Clicking search button...")
            search_btn.click()
            
            # Wait for results using explicit wait
            print("⏳ Waiting for results...")
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
            except:
                pass  # Continue anyway
            
            # Parse results
            print("📊 Parsing results...")
            return self._parse_cnr_results()
            
        except Exception as e:
            print(f"❌ Error during CNR search: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def search_by_case_number(self, state_code: str, dist_code: str, 
                              case_type: str, case_no: str, case_year: str) -> Optional[List[Dict]]:
        """
        Search by case number
        
        Args:
            state_code: State code
            dist_code: District code
            case_type: Case type
            case_no: Case number
            case_year: Case year
            
        Returns:
            List of case dictionaries
        """
        try:
            print(f"🔍 Searching for case: {case_type}/{case_no}/{case_year}")
            
            # Navigate to case status page
            self.driver.get(self.CASE_STATUS_URL)
            
            # Select state
            try:
                state_select = Select(WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "sess_state_code"))
                ))
                state_select.select_by_value(state_code)
            except:
                print("❌ Could not select state")
                return None
            
            # Select district
            try:
                dist_select = Select(WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "sess_dist_code"))
                ))
                dist_select.select_by_value(dist_code)
            except:
                print("❌ Could not select district")
                return None
            
            # Fill case details
            try:
                case_type_select = Select(self.driver.find_element(By.ID, "case_type"))
                case_type_select.select_by_visible_text(case_type)
                
                case_no_input = self.driver.find_element(By.ID, "case_no")
                case_no_input.clear()
                case_no_input.send_keys(case_no)
                
                case_year_input = self.driver.find_element(By.ID, "case_year")
                case_year_input.clear()
                case_year_input.send_keys(case_year)
            except:
                print("❌ Could not fill case details")
                return None
            
            # Handle CAPTCHA
            if not self.headless:
                print("⚠️  Please solve CAPTCHA if present...")
                time.sleep(5)  # Further reduced
            
            # Click search
            try:
                search_btn = self.driver.find_element(By.ID, "search_btn")
                search_btn.click()
                time.sleep(0.5)  # Minimal delay
            except:
                print("❌ Could not click search button")
                return None
            
            # Parse results
            return self._parse_case_results()
            
        except Exception as e:
            print(f"❌ Error during case search: {e}")
            return None
    
    def _parse_cnr_results(self) -> Optional[Dict]:
        """Parse CNR search results - Enhanced to extract all available data"""
        try:
            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Initialize comprehensive case data structure with all fields
            case_data = {
                "cnr_number": None,
                "case_number": None,
                "filing_number": None,
                "registration_number": None,
                "case_type": None,
                "filing_date": None,
                "registration_date": None,
                "first_hearing_date": None,
                "next_hearing_date": None,
                "case_stage": None,
                "court_number_and_judge": None,
                "petitioner_name": None,
                "petitioner_advocate": None,
                "respondent_name": None,
                "respondent_advocate": None,
                "court_name": None,
                "court_number": None,
                "judge_name": None,
                "state": None,
                "district": None,
                "status": None,
                "decision": None,
                "disposal_nature": None,
                "acts": None,
                "under_acts": None,
                "under_sections": None,
                "case_history": [],
                "petitioner_address": None,
                "respondent_address": None,
                "police_station": None,
                "fir_number": None
            }
            
            print("📊 Parsing case details...")
            
            # Try to find case details in various table formats
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True) if cells[1].get_text(strip=True) else None
                        
                        if not value:  # Skip empty values
                            continue
                        
                        # Use more specific matching with priority order
                        # Most specific matches first to avoid misclassification
                        
                        # Petitioner Advocate (check before petitioner)
                        if 'petitioner' in label and 'advocate' in label:
                            if not case_data['petitioner_advocate']:
                                case_data['petitioner_advocate'] = value
                        # Respondent Advocate (check before respondent)
                        elif 'respondent' in label and 'advocate' in label:
                            if not case_data['respondent_advocate']:
                                case_data['respondent_advocate'] = value
                        # CNR Number (exact match)
                        elif label in ['cnr number', 'cnr no', 'cnr no.', 'cnr']:
                            if not case_data['cnr_number']:
                                case_data['cnr_number'] = value
                        # Filing Number
                        elif label in ['filing number', 'filing no', 'filing no.']:
                            if not case_data['filing_number']:
                                case_data['filing_number'] = value
                        # Registration Number
                        elif label in ['registration number', 'registration no', 'registration no.']:
                            if not case_data['registration_number']:
                                case_data['registration_number'] = value
                        # Case Number (specific)
                        elif label in ['case number', 'case no', 'case no.', 'diary number']:
                            if not case_data['case_number']:
                                case_data['case_number'] = value
                        # Case Type
                        elif label in ['case type', 'type of case']:
                            if not case_data['case_type']:
                                case_data['case_type'] = value
                        # Filing Date
                        elif label in ['filing date', 'date of filing']:
                            if not case_data['filing_date']:
                                case_data['filing_date'] = value
                        # Registration Date
                        elif label in ['registration date', 'date of registration']:
                            if not case_data['registration_date']:
                                case_data['registration_date'] = value
                        # First Hearing Date
                        elif label in ['first hearing date', 'date of first hearing']:
                            if not case_data['first_hearing_date']:
                                case_data['first_hearing_date'] = value
                        # Next Hearing Date
                        elif label in ['next hearing date', 'date of next hearing', 'next date']:
                            if not case_data['next_hearing_date']:
                                case_data['next_hearing_date'] = value
                        # Petitioner Name
                        elif 'petitioner' in label and 'name' in label:
                            if not case_data['petitioner_name']:
                                case_data['petitioner_name'] = value
                        elif label == 'petitioner':
                            if not case_data['petitioner_name']:
                                case_data['petitioner_name'] = value
                        # Respondent Name
                        elif 'respondent' in label and 'name' in label:
                            if not case_data['respondent_name']:
                                case_data['respondent_name'] = value
                        elif label == 'respondent':
                            if not case_data['respondent_name']:
                                case_data['respondent_name'] = value
                        # Court Name
                        elif label in ['court name', 'name of court', 'court']:
                            if not case_data['court_name']:
                                case_data['court_name'] = value
                        # Court Number
                        elif label in ['court number', 'court no', 'court no.']:
                            if not case_data['court_number']:
                                case_data['court_number'] = value
                        # Judge Name
                        elif label in ['judge name', 'name of judge', 'judge', 'judicial officer']:
                            if not case_data['judge_name']:
                                case_data['judge_name'] = value
                        # State
                        elif label == 'state' or label == 'state name':
                            if not case_data['state']:
                                case_data['state'] = value
                        # District
                        elif label == 'district' or label == 'district name':
                            if not case_data['district']:
                                case_data['district'] = value
                        # Case Status
                        elif label in ['case status', 'status']:
                            if not case_data['status']:
                                case_data['status'] = value
                        # Case Stage
                        elif label in ['case stage', 'stage', 'stage of case']:
                            if not case_data['case_stage']:
                                case_data['case_stage'] = value
                        # Court Number and Judge (combined field)
                        elif label in ['court number and judge', 'court no and judge', 'court & judge']:
                            if not case_data['court_number_and_judge']:
                                case_data['court_number_and_judge'] = value
                        # Decision
                        elif label in ['decision', 'disposal']:
                            if not case_data['decision']:
                                case_data['decision'] = value
                        # Disposal Nature
                        elif label in ['nature of disposal', 'disposal nature']:
                            if not case_data['disposal_nature']:
                                case_data['disposal_nature'] = value
                        # Under Acts
                        elif label in ['under act(s)', 'under acts', 'act(s)']:
                            if not case_data['under_acts']:
                                case_data['under_acts'] = value
                        # Under Sections
                        elif label in ['under section(s)', 'under sections', 'section(s)']:
                            if not case_data['under_sections']:
                                case_data['under_sections'] = value
                        # Acts and Sections (combined)
                        elif 'act' in label and 'section' in label:
                            if not case_data['acts']:
                                case_data['acts'] = value
                        elif label in ['acts', 'sections']:
                            if not case_data['acts']:
                                case_data['acts'] = value
                        # Petitioner Address
                        elif 'petitioner' in label and 'address' in label:
                            if not case_data['petitioner_address']:
                                case_data['petitioner_address'] = value
                        # Respondent Address
                        elif 'respondent' in label and 'address' in label:
                            if not case_data['respondent_address']:
                                case_data['respondent_address'] = value
                        # Police Station
                        elif label in ['police station', 'ps', 'p.s.']:
                            if not case_data['police_station']:
                                case_data['police_station'] = value
                        # FIR Number
                        elif label in ['fir number', 'fir no', 'fir no.', 'fir']:
                            if not case_data['fir_number']:
                                case_data['fir_number'] = value
            
            # Try to extract case history/proceedings
            history_found = False
            for table in tables:
                # Look for history table headers
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])
                
                if 'date' in header_text and ('business' in header_text or 'order' in header_text or 'purpose' in header_text):
                    history_found = True
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            history_item = {
                                'date': cells[0].get_text(strip=True) if len(cells) > 0 else None,
                                'description': cells[1].get_text(strip=True) if len(cells) > 1 else None
                            }
                            if history_item['date']:
                                case_data['case_history'].append(history_item)
            
            # Debug: Print what we found
            found_fields = {k: v for k, v in case_data.items() if v and k != 'case_history'}
            print(f"✅ Extracted {len(found_fields)} fields")
            if case_data['case_history']:
                print(f"✅ Found {len(case_data['case_history'])} history entries")
            
            # Check if we got any meaningful data
            if case_data['cnr_number'] or case_data['case_number'] or any(found_fields.values()):
                print("✅ Case data extracted successfully!")
                return case_data
            else:
                print("❌ No case data found in results")
                # Save debug HTML
                with open('debug_results.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("📝 Saved page source to debug_results.html for inspection")
                return None
                
        except Exception as e:
            print(f"❌ Error parsing results: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_case_results(self) -> Optional[List[Dict]]:
        """Parse case number search results"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            cases = []
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        case = {
                            "case_number": cells[0].get_text(strip=True) if len(cells) > 0 else None,
                            "petitioner": cells[1].get_text(strip=True) if len(cells) > 1 else None,
                            "respondent": cells[2].get_text(strip=True) if len(cells) > 2 else None,
                            "status": cells[3].get_text(strip=True) if len(cells) > 3 else None,
                        }
                        cases.append(case)
            
            if cases:
                print(f"✅ Found {len(cases)} case(s)")
                return cases
            else:
                print("❌ No cases found")
                return None
                
        except Exception as e:
            print(f"❌ Error parsing case results: {e}")
            return None
    
    def get_states(self) -> List[Dict]:
        """Get list of available states"""
        try:
            self.driver.get(self.CASE_STATUS_URL)
            
            state_select = Select(self.driver.find_element(By.ID, "sess_state_code"))
            states = []
            
            for option in state_select.options:
                if option.get_attribute('value'):
                    states.append({
                        'code': option.get_attribute('value'),
                        'name': option.text
                    })
            
            return states
        except:
            return []
    
    def get_districts(self, state_code: str) -> List[Dict]:
        """Get list of districts for a state"""
        try:
            self.driver.get(self.CASE_STATUS_URL)
            
            # Select state first
            state_select = Select(self.driver.find_element(By.ID, "sess_state_code"))
            state_select.select_by_value(state_code)
            
            # Get districts
            dist_select = Select(self.driver.find_element(By.ID, "sess_dist_code"))
            districts = []
            
            for option in dist_select.options:
                if option.get_attribute('value'):
                    districts.append({
                        'code': option.get_attribute('value'),
                        'name': option.text
                    })
            
            return districts
        except:
            return []
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
    
    def __del__(self):
        """Cleanup"""
        self.close()
