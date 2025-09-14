#!/usr/bin/env python3
"""Debug script to test WPRM recipe extraction specifically"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import requests
from bs4 import BeautifulSoup
from server import extract_structured_content

# Test data
food_text = """spicy peanut butter noodles: -Shin ramyun noodles
-Peanut butter (smooth shown here although use crunchy if you prefer)
-Chilli oil
Follow the instructions from the noodle packet for cooking them.
Empty the sachets from the noodles in a bowl and put in peanut butter and chilli oil and mix and then fill with boiling water and mix (I prefer to use the water I cooked the noodles in)
Then put in the noodles and mix to coat them in the sauce.
Unless you can handle some heat, limit how much of the noodles sachet you put in and chilli oil as it has quite a kick to it!"""

def test_config():
    """Test if config is loading properly"""
    print("=== CONFIGURATION TEST ===")
    cfg = config.get_config()
    print(f"Environment: {cfg.ENVIRONMENT}")
    print(f"OpenAI API Key present: {'Yes' if cfg.OPENAI_API_KEY else 'No'}")
    print(f"OpenAI API Key (first 10 chars): {cfg.OPENAI_API_KEY[:10] if cfg.OPENAI_API_KEY else 'None'}")
    print(f"Brave API Key present: {'Yes' if cfg.BRAVE_API_KEY else 'No'}")
    print(f"Brave API Key (first 10 chars): {cfg.BRAVE_API_KEY[:10] if cfg.BRAVE_API_KEY else 'None'}")
    print(f"OpenAI Model: {cfg.OPENAI_MODEL}")
    return cfg

def test_theme_detection():
    """Test theme detection function"""
    print("\n=== THEME DETECTION TEST ===")
    try:
        detected_theme = extract_theme(food_text)
        print(f"Detected theme: '{detected_theme}'")
        print(f"Expected theme: 'food'")
        print(f"Test result: {'PASS' if detected_theme == 'food' else 'FAIL'}")
        return detected_theme
    except Exception as e:
        print(f"Theme detection failed with error: {e}")
        return None

def test_web_search():
    """Test web search function"""
    print("\n=== WEB SEARCH TEST ===")
    test_queries = [
        "spicy peanut butter noodles recipe",
        "latest insights spicy peanut butter noodles: -Shin ramyun noodles -Peanut"  # Actual query format
    ]

    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        try:
            results = web_search(query, num_results=2)
            print(f"Number of results: {len(results)}")

            if results:
                for i, result in enumerate(results, 1):
                    print(f"  [{i}] Title: {result.get('title', 'No title')}")
                    print(f"      URL: {result.get('url', 'No URL')}")
                    print(f"      Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            else:
                print("  No results returned")

        except Exception as e:
            print(f"Web search failed with error: {e}")

if __name__ == "__main__":
    print("DEBUGGING FOOD THEME AND CITATION ISSUES")
    print("=" * 50)

    # Test configuration
    cfg = test_config()

    # Test theme detection
    theme = test_theme_detection()

    # Test web search
    test_web_search()

    print("\n=== SUMMARY ===")
    if theme == "food":
        print("✓ Theme detection working correctly")
    else:
        print("✗ Theme detection issue - should be 'food'")

    print("\nIf web search returned results, citation system should work.")
    print("If no results, check Brave API configuration.")