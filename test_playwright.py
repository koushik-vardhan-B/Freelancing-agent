"""
TEST 1: Playwright Sanity Check (SYNC VERSION)

Uses sync_playwright to avoid Windows asyncio issues.

Usage:
    python test_playwright.py
"""

from playwright.sync_api import sync_playwright


def main():
    print("Testing Playwright (sync mode)...")
    print("-" * 40)
    
    try:
        with sync_playwright() as p:
            print("[OK] Playwright started")
            
            browser = p.chromium.launch(headless=True)
            print("[OK] Browser launched")
            
            page = browser.new_page()
            print("[OK] Page created")
            
            page.goto("https://example.com")
            print("[OK] Navigated to example.com")
            
            title = page.title()
            print(f"[OK] Page title: {title}")
            
            browser.close()
            print("[OK] Browser closed")
        
        print("-" * 40)
        print("SUCCESS: PLAYWRIGHT WORKS!")
        print("\nYou can now run the full scraper.")
        
    except Exception as e:
        print(f"[FAIL]: {e}")
        print("\nTry running: playwright install chromium")


if __name__ == "__main__":
    main()
