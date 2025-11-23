#!/usr/bin/env python3
"""
Debug script to see exactly what ScrapingBee returns
"""

import requests
import json

def debug_scrapingbee_response(url: str):
    """
    Debug what ScrapingBee actually returns
    """
    api_url = "https://app.scrapingbee.com/api/v1/"
    api_key = "P4D419SLNCIC982UXCMNA4PN634NSQ2P4BNKAIXX7X7NKU42JIQRT8INEOK66S9TEDZBQWRH3MLU06AB"
    
    # Test 1: Basic request with just markdown
    print("=== TEST 1: Basic markdown request ===")
    params1 = {
        "api_key": api_key,
        "url": url,
        "render_js": "true",
        "return_page_markdown": "true"
    }
    
    response1 = requests.get(api_url, params=params1, timeout=60)
    print(f"Status: {response1.status_code}")
    print(f"Content-Type: {response1.headers.get('content-type', 'Unknown')}")
    print(f"Response length: {len(response1.text)}")
    print(f"First 200 chars: {response1.text[:200]}")
    print()
    
    # Test 2: With extraction rules
    print("=== TEST 2: With extraction rules ===")
    extract_rules = {
        "title": "h1, .article-title, .post-title, title", 
        "author": ".author, .byline, .post-author, [rel='author']", 
        "date": ".date, .published, .post-date, time[datetime]"
    }
    
    params2 = {
        "api_key": api_key,
        "url": url,
        "render_js": "true",
        "return_page_markdown": "true",
        "extract_rules": json.dumps(extract_rules)
    }
    
    response2 = requests.get(api_url, params=params2, timeout=60)
    print(f"Status: {response2.status_code}")
    print(f"Content-Type: {response2.headers.get('content-type', 'Unknown')}")
    print(f"Response length: {len(response2.text)}")
    print(f"First 200 chars: {response2.text[:200]}")
    
    # Try to parse as JSON
    try:
        json_data = response2.json()
        print("✅ Response is valid JSON!")
        print(f"JSON keys: {list(json_data.keys())}")
        if 'extracted' in json_data:
            print(f"Extracted data: {json_data['extracted']}")
        if 'markdown' in json_data:
            print(f"Markdown length: {len(json_data.get('markdown', ''))}")
    except json.JSONDecodeError:
        print("❌ Response is not JSON")
    
    print()
    
    # Test 3: Just extraction rules (no markdown)
    print("=== TEST 3: Just extraction rules ===")
    params3 = {
        "api_key": api_key,
        "url": url,
        "render_js": "true",
        "extract_rules": json.dumps(extract_rules)
    }
    
    response3 = requests.get(api_url, params=params3, timeout=60)
    print(f"Status: {response3.status_code}")
    print(f"Content-Type: {response3.headers.get('content-type', 'Unknown')}")
    print(f"Response length: {len(response3.text)}")
    print(f"First 200 chars: {response3.text[:200]}")
    
    try:
        json_data = response3.json()
        print("✅ Response is valid JSON!")
        print(f"JSON keys: {list(json_data.keys())}")
        if 'extracted' in json_data:
            print(f"Extracted data: {json_data['extracted']}")
    except json.JSONDecodeError:
        print("❌ Response is not JSON")

if __name__ == "__main__":
    url = "https://investopedia.com/broker/robinhood-review"
    debug_scrapingbee_response(url)
