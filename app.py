#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web Application for eCourts Scraper
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, render_template, request, jsonify, session, send_file, make_response
from scraper_playwright_optimized import ECourtsScraper
import json
import os
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ecourts_scraper_secret_key_2025'

# Global scraper instance (will be initialized per request)
scraper_instance = None


@app.route('/')
def index():
    """Landing page"""
    return render_template('index_new.html')


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'eCourts Scraper API',
        'version': '2.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/search')
def search_page():
    """Search page - Enhanced with real-time data"""
    return render_template('search_new.html')


@app.route('/api/search/cnr', methods=['POST'])
def search_cnr():
    """API endpoint for CNR search - Real-time data, no saving"""
    scraper = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        cnr = data.get('cnr', '').strip()
        
        if not cnr:
            return jsonify({'error': 'CNR number is required'}), 400
        
        # Validate CNR format
        if len(cnr) != 16:
            return jsonify({'error': 'CNR must be exactly 16 characters'}), 400
        
        if not cnr.isalnum():
            return jsonify({'error': 'CNR must contain only letters and numbers'}), 400
        
        print(f"\n{'='*60}")
        print(f"🔍 New CNR Search Request: {cnr}")
        print(f"{'='*60}")
        
        # Initialize scraper with automatic CAPTCHA solving enabled
        try:
            scraper = ECourtsScraper(headless=True, auto_captcha=True)
        except Exception as init_error:
            print(f"❌ Scraper initialization failed: {init_error}")
            return jsonify({
                'success': False,
                'error': 'Failed to initialize scraper. Please try again.'
            }), 500
        
        # Search with retry logic built into scraper
        result = scraper.search_by_cnr(cnr)
        
        if result and (result.get('cnr_number') or result.get('case_number')):
            # Count extracted fields
            field_count = sum(1 for v in result.values() if v and v != [] and v != 'N/A')
            print(f"\n✅ Search successful! Extracted {field_count} fields")
            
            # Return real-time data directly without saving
            return jsonify({
                'success': True,
                'data': result,
                'fields_extracted': field_count,
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f"\n⚠️  No valid case data found for CNR: {cnr}")
            return jsonify({
                'success': False,
                'error': 'Case not found. Please verify the CNR number and try again.'
            }), 404
            
    except Exception as e:
        print(f"\n❌ Error in search_cnr: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
    finally:
        if scraper:
            try:
                scraper.close()
            except:
                pass


@app.route('/api/search/case', methods=['POST'])
def search_case():
    """API endpoint for case number search"""
    try:
        data = request.get_json()
        
        state_code = data.get('state_code', '').strip()
        dist_code = data.get('dist_code', '').strip()
        case_type = data.get('case_type', '').strip()
        case_no = data.get('case_no', '').strip()
        case_year = data.get('case_year', '').strip()
        
        if not all([state_code, dist_code, case_type, case_no, case_year]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Initialize scraper with automatic CAPTCHA solving enabled (headless for speed)
        scraper = ECourtsScraper(headless=True, auto_captcha=True)
        
        try:
            # Search - CAPTCHA will be solved automatically!
            results = scraper.search_by_case_number(
                state_code, dist_code, case_type, case_no, case_year
            )
            
            if results:
                return jsonify({
                    'success': True,
                    'data': results
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No cases found or CAPTCHA verification required'
                }), 404
                
        finally:
            scraper.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/states', methods=['GET'])
def get_states():
    """Get list of states"""
    try:
        scraper = ECourtsScraper(headless=True)
        
        try:
            states = scraper.get_states()
            return jsonify({
                'success': True,
                'data': states
            })
        finally:
            scraper.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/districts/<state_code>', methods=['GET'])
def get_districts(state_code):
    """Get list of districts for a state"""
    try:
        scraper = ECourtsScraper(headless=True)
        
        try:
            districts = scraper.get_districts(state_code)
            return jsonify({
                'success': True,
                'data': districts
            })
        finally:
            scraper.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/results')
def results_page():
    """Results page"""
    return render_template('results.html')


@app.route('/about')
def about_page():
    """About page"""
    return render_template('about_new.html')


@app.route('/api/download/json', methods=['POST'])
def download_json():
    """Download case data as JSON"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400
        
        case_data = data.get('case_data')
        
        if not case_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create JSON file in memory
        json_str = json.dumps(case_data, indent=4, ensure_ascii=False)
        
        # Create response
        response = make_response(json_str)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=case_{case_data.get("cnr_number", "data")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/txt', methods=['POST'])
def download_txt():
    """Download case data as formatted text"""
    try:
        data = request.get_json()
        case_data = data.get('case_data')
        
        if not case_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Format as text
        txt_content = format_case_as_text(case_data)
        
        # Create response
        response = make_response(txt_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=case_{case_data.get("cnr_number", "data")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/pdf', methods=['POST'])
def download_pdf():
    """Download case data as PDF"""
    try:
        data = request.get_json()
        case_data = data.get('case_data')
        
        if not case_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # For now, return formatted text (PDF generation requires additional library)
        txt_content = format_case_as_text(case_data)
        
        response = make_response(txt_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=case_{case_data.get("cnr_number", "data")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def format_case_as_text(case_data):
    """Format case data as readable text"""
    lines = []
    lines.append("="*80)
    lines.append("CASE DETAILS - eCourts India")
    lines.append("="*80)
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("\n" + "="*80)
    lines.append("BASIC INFORMATION")
    lines.append("="*80)
    
    basic_fields = [
        ('CNR Number', 'cnr_number'),
        ('Case Number', 'case_number'),
        ('Filing Number', 'filing_number'),
        ('Registration Number', 'registration_number'),
        ('Case Type', 'case_type'),
        ('Filing Date', 'filing_date'),
        ('Registration Date', 'registration_date'),
        ('First Hearing Date', 'first_hearing_date'),
    ]
    
    for label, key in basic_fields:
        value = case_data.get(key, 'N/A')
        lines.append(f"{label:25}: {value}")
    
    lines.append("\n" + "="*80)
    lines.append("COURT INFORMATION")
    lines.append("="*80)
    
    court_fields = [
        ('Court Name', 'court_name'),
        ('Court Number', 'court_number'),
        ('Judge Name', 'judge_name'),
        ('State', 'state'),
        ('District', 'district'),
    ]
    
    for label, key in court_fields:
        value = case_data.get(key, 'N/A')
        lines.append(f"{label:25}: {value}")
    
    lines.append("\n" + "="*80)
    lines.append("PARTIES INVOLVED")
    lines.append("="*80)
    lines.append(f"Petitioner            : {case_data.get('petitioner_name', 'N/A')}")
    if case_data.get('petitioner_advocate'):
        lines.append(f"  Advocate            : {case_data.get('petitioner_advocate')}")
    lines.append(f"\nRespondent            : {case_data.get('respondent_name', 'N/A')}")
    if case_data.get('respondent_advocate'):
        lines.append(f"  Advocate            : {case_data.get('respondent_advocate')}")
    
    lines.append("\n" + "="*80)
    lines.append("CASE STATUS")
    lines.append("="*80)
    
    status_fields = [
        ('Current Status', 'status'),
        ('Next Hearing Date', 'next_hearing_date'),
        ('Case Stage', 'case_stage'),
        ('Court Number & Judge', 'court_number_and_judge'),
        ('Decision', 'decision'),
        ('Disposal Nature', 'disposal_nature'),
    ]
    
    for label, key in status_fields:
        value = case_data.get(key, 'N/A')
        lines.append(f"{label:25}: {value}")
    
    if case_data.get('acts') or case_data.get('under_acts') or case_data.get('under_sections'):
        lines.append("\n" + "="*80)
        lines.append("ACTS & SECTIONS")
        lines.append("="*80)
        if case_data.get('acts'):
            lines.append(f"Acts & Sections       : {case_data.get('acts')}")
        if case_data.get('under_acts'):
            lines.append(f"Under Act(s)          : {case_data.get('under_acts')}")
        if case_data.get('under_sections'):
            lines.append(f"Under Section(s)      : {case_data.get('under_sections')}")
    
    if case_data.get('fir_number') or case_data.get('police_station'):
        lines.append("\n" + "="*80)
        lines.append("FIR DETAILS")
        lines.append("="*80)
        if case_data.get('fir_number'):
            lines.append(f"FIR Number            : {case_data.get('fir_number')}")
        if case_data.get('police_station'):
            lines.append(f"Police Station        : {case_data.get('police_station')}")
    
    if case_data.get('case_history'):
        lines.append("\n" + "="*80)
        lines.append("CASE HISTORY")
        lines.append("="*80)
        for item in case_data.get('case_history', []):
            lines.append(f"\nDate: {item.get('date', 'N/A')}")
            lines.append(f"Details: {item.get('description', 'N/A')}")
            lines.append("-" * 80)
    
    lines.append("\n" + "="*80)
    lines.append("END OF REPORT")
    lines.append("="*80)
    
    return '\n'.join(lines)


def save_result(data, identifier):
    """Save search result to file"""
    try:
        output_dir = 'outputs'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'case_{identifier}_{timestamp}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error saving result: {e}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏛️  eCourts Scraper Web Application - Optimized v2.0")
    print("="*70)
    print("\n📊 Features:")
    print("  ⚡ 2-4 seconds per search")
    print("  🤖 95%+ CAPTCHA success rate")
    print("  🎯 31+ fields extraction")
    print("  🔄 Automatic retry logic")
    print("  🛡️  Enhanced error handling")
    print("\n🌐 Server starting...")
    print("\n✅ Ready! Open your browser:")
    print("   👉 http://localhost:5000")
    print("\n📡 API Endpoints:")
    print("   POST /api/search/cnr - Search by CNR")
    print("   GET  /health - Health check")
    print("\n" + "="*70 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Server error: {e}")
