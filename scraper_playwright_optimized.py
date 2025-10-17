#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eCourts Web Scraper - Optimized Playwright Version
High-performance scraper with precise field mapping
"""

import time
import re
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple

# Import CAPTCHA solver
try:
    from captcha_solver import CaptchaSolver
    CAPTCHA_SOLVER_AVAILABLE = True
except ImportError:
    CAPTCHA_SOLVER_AVAILABLE = False
    print("⚠️  CAPTCHA solver not available. Install: pip install easyocr Pillow opencv-python")


class ECourtsScraper:
    """Optimized web scraper for eCourts India website using Playwright"""
    
    BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"
    CNR_SEARCH_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=home/index"
    CASE_STATUS_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/index"
    
    # Optimized field mapping with multiple label variants
    FIELD_MAPPINGS = {
        'cnr_number': ['cnr number', 'cnr no', 'cnr'],
        'case_number': ['case number', 'case no', 'diary number', 'case no note the cnr number for future reference'],
        'filing_number': ['filing number', 'filing no'],
        'registration_number': ['registration number', 'registration no', 'reg no', 'reg number'],
        'case_type': ['case type', 'type of case'],
        'filing_date': ['filing date', 'date of filing'],
        'registration_date': ['registration date', 'date of registration', 'reg date'],
        'first_hearing_date': ['first hearing date', 'date of first hearing', '1st hearing date'],
        'next_hearing_date': ['next hearing date', 'date of next hearing', 'next date', 'next hearing'],
        'case_stage': ['case stage', 'stage', 'stage of case'],
        'status': ['case status', 'status', 'current status'],
        'decision_date': ['decision date', 'date of decision'],
        'decision': ['decision', 'disposal'],
        'disposal_nature': ['nature of disposal', 'disposal nature'],
        'court_name': ['court name', 'name of court', 'court'],
        'court_number': ['court number', 'court no'],
        'judge_name': ['judge name', 'name of judge', 'judge', 'judicial officer'],
        'state': ['state', 'state name'],
        'district': ['district', 'district name'],
        'petitioner_name': ['petitioner name', 'petitioner'],
        'respondent_name': ['respondent name', 'respondent'],
        'petitioner_advocate': ['petitioner advocate', 'advocate for petitioner'],
        'respondent_advocate': ['respondent advocate', 'advocate for respondent'],
        'under_acts': ['under act s', 'under acts', 'act s', 'acts'],
        'under_sections': ['under section s', 'under sections', 'section s', 'u s'],
        'fir_number': ['fir number', 'fir no', 'fir'],
        'police_station': ['police station', 'ps', 'p s'],
    }
    
    def __init__(self, headless: bool = True, auto_captcha: bool = True):
        """Initialize the scraper with Playwright"""
        self.headless = headless
        self.auto_captcha = auto_captcha
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.captcha_solver = None
        
        # Initialize CAPTCHA solver if available
        if auto_captcha and CAPTCHA_SOLVER_AVAILABLE:
            self.captcha_solver = CaptchaSolver()
            if self.captcha_solver.is_easyocr_available():
                print("✅ Automatic CAPTCHA solving enabled (EasyOCR)")
            else:
                print("⚠️  EasyOCR not available - CAPTCHA solving disabled")
                self.captcha_solver = None
        
        self._init_browser()
    
    def _init_browser(self):
        """Initialize Playwright browser with optimizations"""
        try:
            print("🔧 Initializing Playwright browser...")
            
            self.playwright = sync_playwright().start()
            
            # Launch browser with performance optimizations
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-web-security',
                    '--window-size=1920,1080'
                ]
            )
            
            # Create context with optimizations
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            # Block heavy resources except CAPTCHA
            def route_filter(route):
                req = route.request
                rtype = req.resource_type
                url = req.url.lower()
                
                # Always allow CAPTCHA
                if 'captcha' in url:
                    return route.continue_()
                
                # Block heavy resources
                if rtype in ['font', 'media', 'image']:
                    return route.abort()
                
                # Allow everything else
                return route.continue_()
            
            self.context.route("**/*", route_filter)
            
            # Create page
            self.page = self.context.new_page()
            self.page.set_default_timeout(15000)  # 15 seconds
            
            print("✅ Browser initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            raise
    
    def _normalize_label(self, label: str) -> str:
        """Normalize label for matching"""
        return re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
    
    def _match_field(self, label: str) -> Optional[str]:
        """Match label to field name using optimized mapping"""
        norm_label = self._normalize_label(label)
        
        # Direct mapping lookup
        for field, variants in self.FIELD_MAPPINGS.items():
            if norm_label in variants:
                return field
        
        # Partial matching for complex labels
        if 'court number' in norm_label and 'judge' in norm_label:
            return 'court_number_and_judge'
        if 'petitioner' in norm_label and 'advocate' in norm_label:
            return 'petitioner_advocate'
        if 'respondent' in norm_label and 'advocate' in norm_label:
            return 'respondent_advocate'
        if 'act' in norm_label and 'section' in norm_label:
            return 'acts'
        if 'petitioner' in norm_label and 'address' in norm_label:
            return 'petitioner_address'
        if 'respondent' in norm_label and 'address' in norm_label:
            return 'respondent_address'
        
        return None
    
    def search_by_cnr(self, cnr: str) -> Optional[Dict]:
        """Search case by CNR number with optimized flow"""
        try:
            print(f"\n🔍 Searching for CNR: {cnr}")
            
            # Navigate to CNR search page
            print("📄 Loading CNR search page...")
            self.page.goto(self.CNR_SEARCH_URL, wait_until='domcontentloaded')
            self.page.wait_for_load_state('networkidle', timeout=5000)
            
            print("✅ Page loaded")
            
            # Find and fill CNR input
            print("📝 Entering CNR number...")
            cnr_input = self.page.wait_for_selector(
                'input[name="cnr_number"], input#cnr_number, input[placeholder*="CNR" i]',
                timeout=3000
            )
            
            if not cnr_input:
                print("❌ Could not find CNR input field")
                return None
            
            cnr_input.fill(cnr)
            print("✅ CNR entered")
            
            # Handle CAPTCHA
            if self.captcha_solver and self.auto_captcha:
                print("🤖 Attempting automatic CAPTCHA solving...")
                if self._solve_captcha_playwright():
                    print("✅ CAPTCHA solved automatically!")
                    time.sleep(1)
                else:
                    print("❌ Automatic CAPTCHA solving failed")
                    print("⏳ Waiting 8 seconds for manual input...")
                    time.sleep(8)
            else:
                print("⏳ Waiting 8 seconds for manual input...")
                time.sleep(8)
            
            # Click search button
            print("🔍 Clicking search button...")
            search_button = self.page.wait_for_selector(
                'button[type="submit"], input[type="submit"], button:has-text("Search")',
                timeout=3000
            )
            search_button.click()
            print("✅ Search initiated")
            
            # Wait for results
            print("⏳ Waiting for results...")
            try:
                self.page.wait_for_selector('table', timeout=6000)
                print("✅ Results loaded")
            except:
                print("⚠️  No results table found, trying to parse anyway...")
            
            # Parse results
            return self._parse_cnr_results()
            
        except Exception as e:
            print(f"❌ Error during CNR search: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _solve_captcha_playwright(self) -> bool:
        """Solve CAPTCHA using Playwright"""
        try:
            # Find CAPTCHA image
            captcha_img = self.page.query_selector('img[src*="captcha"], img#captcha_image, img.captcha')
            
            if not captcha_img:
                return False
            
            # Take screenshot
            captcha_screenshot_path = 'captcha_screenshot.png'
            captcha_img.screenshot(path=captcha_screenshot_path)
            
            # Extract text
            captcha_text = self.captcha_solver.extract_text_from_image(captcha_screenshot_path)
            
            if not captcha_text:
                return False
            
            print(f"✅ CAPTCHA text extracted: '{captcha_text}'")
            
            # Fill CAPTCHA input
            captcha_input = self.page.query_selector(
                'input[name="captcha"], input#captcha, input[placeholder*="captcha" i]'
            )
            
            if not captcha_input:
                return False
            
            captcha_input.fill(captcha_text)
            return True
            
        except Exception as e:
            print(f"❌ Error solving CAPTCHA: {e}")
            return False
    
    def _parse_cnr_results(self) -> Optional[Dict]:
        """Optimized parsing with precise field mapping"""
        try:
            # Get page content
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Initialize case data
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
                "decision_date": None,
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
            
            # Parse all tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if not value:
                            continue
                        
                        # Match field using optimized mapping
                        field = self._match_field(label)
                        
                        if field and not case_data[field]:
                            case_data[field] = value
                        
                        # Handle combined parties row
                        if ('petitioner' in label.lower() and 'respondent' in label.lower()) or 'parties' in label.lower():
                            parts = re.split(r"\bvs\b|\bv\.?\b|\bversus\b|/", value, flags=re.IGNORECASE)
                            if len(parts) >= 2:
                                if not case_data['petitioner_name']:
                                    case_data['petitioner_name'] = parts[0].strip()
                                if not case_data['respondent_name']:
                                    case_data['respondent_name'] = parts[1].strip()
            
            # Extract case history
            for table in tables:
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])
                
                if 'date' in header_text and ('business' in header_text or 'order' in header_text or 'purpose' in header_text or 'hearing' in header_text):
                    rows = table.find_all('tr')[1:]
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            history_item = {
                                'date': cells[0].get_text(strip=True),
                                'description': cells[1].get_text(strip=True)
                            }
                            if history_item['date']:
                                case_data['case_history'].append(history_item)
            
            # Parse section-specific blocks
            self._parse_case_status_section(soup, case_data)
            self._parse_parties_section(soup, case_data)
            self._parse_acts_section(soup, case_data)
            
            # Post-processing
            self._post_process_fields(case_data)
            
            # Debug output
            found_fields = {k: v for k, v in case_data.items() if v and k != 'case_history'}
            print(f"✅ Extracted {len(found_fields)} fields")
            if case_data['case_history']:
                print(f"✅ Found {len(case_data['case_history'])} history entries")
            
            # Check if we got meaningful data
            if case_data['cnr_number'] or case_data['case_number'] or any(found_fields.values()):
                print("✅ Case data extracted successfully!")
                return case_data
            else:
                print("❌ No case data found in results")
                with open('debug_results.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("📝 Saved page source to debug_results.html")
                return None
                
        except Exception as e:
            print(f"❌ Error parsing results: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_case_status_section(self, soup: BeautifulSoup, case_data: Dict):
        """Parse Case Status section specifically"""
        # Find "Case Status" heading
        status_nodes = soup.find_all(text=re.compile(r'^\s*Case\s*Status\s*$', re.I))
        
        for node in status_nodes:
            # Find next table
            parent = node.parent
            for _ in range(5):
                if parent and parent.name == 'table':
                    break
                parent = parent.find_next_sibling() if parent else None
            
            if parent and parent.name == 'table':
                for row in parent.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if not value:
                            continue
                        
                        field = self._match_field(label)
                        if field and not case_data[field]:
                            case_data[field] = value
    
    def _parse_parties_section(self, soup: BeautifulSoup, case_data: Dict):
        """Parse Petitioner and Respondent sections"""
        # Petitioner and Advocate
        pet_nodes = soup.find_all(text=re.compile(r'Petitioner\s*and\s*Advocate', re.I))
        for node in pet_nodes:
            text = self._get_sibling_text(node, 6)
            # Pattern: 1) NAME  Advocate: LAWYER
            match = re.search(r'\)\s*([^\n]+?)\s+Advocate\s*:\s*([^\n]+)', text, re.I)
            if match:
                if not case_data['petitioner_name']:
                    case_data['petitioner_name'] = match.group(1).strip()
                if not case_data['petitioner_advocate']:
                    case_data['petitioner_advocate'] = match.group(2).strip()
        
        # Respondent and Advocate
        resp_nodes = soup.find_all(text=re.compile(r'Respondent\s*and\s*Advocate', re.I))
        for node in resp_nodes:
            text = self._get_sibling_text(node, 6)
            match = re.search(r'\)\s*([^\n]+?)\s+Advocate\s*:\s*([^\n]+)', text, re.I)
            if match:
                if not case_data['respondent_name']:
                    case_data['respondent_name'] = match.group(1).strip()
                if not case_data['respondent_advocate']:
                    case_data['respondent_advocate'] = match.group(2).strip()
    
    def _parse_acts_section(self, soup: BeautifulSoup, case_data: Dict):
        """Parse Acts section"""
        acts_nodes = soup.find_all(text=re.compile(r'^\s*Acts\s*$', re.I))
        
        for node in acts_nodes:
            parent = node.parent
            for _ in range(5):
                if parent and parent.name == 'table':
                    break
                parent = parent.find_next_sibling() if parent else None
            
            if parent and parent.name == 'table':
                for row in parent.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if not value:
                            continue
                        
                        field = self._match_field(label)
                        if field and not case_data[field]:
                            case_data[field] = value
    
    def _get_sibling_text(self, node, max_hops: int = 6) -> str:
        """Get text from next siblings"""
        text = ''
        sib = node.parent
        for _ in range(max_hops):
            sib = sib.find_next_sibling() if sib else None
            if sib:
                text += ' ' + sib.get_text(" ", strip=True)
        return text
    
    def _post_process_fields(self, case_data: Dict):
        """Post-process and synthesize fields"""
        # Synthesize acts from under_acts and under_sections
        if not case_data['acts'] and (case_data['under_acts'] or case_data['under_sections']):
            parts = []
            if case_data['under_acts']:
                parts.append(case_data['under_acts'])
            if case_data['under_sections']:
                parts.append(case_data['under_sections'])
            case_data['acts'] = '; '.join(parts)
        
        # Synthesize court_number_and_judge
        if not case_data['court_number_and_judge'] and case_data['court_number'] and case_data['judge_name']:
            case_data['court_number_and_judge'] = f"{case_data['court_number']}-{case_data['judge_name']}"
        
        # Split court_number_and_judge if we have it
        if case_data['court_number_and_judge']:
            cj = case_data['court_number_and_judge']
            
            # Extract court number
            match = re.match(r'\s*(\d+)\s*[-–]', cj)
            if match and not case_data['court_number']:
                case_data['court_number'] = match.group(1)
            
            # Extract judge name
            parts = re.split(r'[-–]', cj, maxsplit=1)
            if len(parts) == 2 and not case_data['judge_name']:
                case_data['judge_name'] = parts[1].strip()
    
    def close(self):
        """Close the browser"""
        try:
            if self.page:
                try:
                    self.page.close()
                except:
                    pass
            if self.context:
                try:
                    self.context.close()
                except:
                    pass
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
            if self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass
            print("✅ Browser closed")
        except Exception as e:
            print(f"⚠️  Error closing browser: {e}")
    
    def __del__(self):
        """Cleanup"""
        try:
            self.close()
        except:
            pass


if __name__ == "__main__":
    # Example usage
    scraper = ECourtsScraper(headless=True, auto_captcha=True)
    
    try:
        # Search by CNR
        cnr = "UPBL060008062016"
        result = scraper.search_by_cnr(cnr)
        
        if result:
            print("\n" + "="*80)
            print("CASE DETAILS")
            print("="*80)
            for key, value in result.items():
                if value and key != 'case_history':
                    print(f"{key:25}: {value}")
            
            if result.get('case_history'):
                print("\nCASE HISTORY:")
                for item in result['case_history']:
                    print(f"  {item['date']}: {item['description']}")
        else:
            print("\n❌ No case found or error occurred")
    
    finally:
        scraper.close()
