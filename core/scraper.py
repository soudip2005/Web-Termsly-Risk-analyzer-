import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

# --- New Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
# -----------------------------

# Keywords to find policy pages
POLICY_KEYWORDS = ['privacy', 'terms', 'policy', 'legal', 'conditions', 'cookie']

def get_selenium_driver():
    """Initializes and returns a headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in the background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # This will automatically download and manage the correct chromedriver
    service = ChromeService(ChromeDriverManager().install())
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error initializing Selenium driver: {e}")
        print("Please ensure Google Chrome is installed on your system.")
        return None
    return driver

def score_link(href, text):
    """Scores a link based on how likely it is to be a main policy page."""
    href = href.lower()
    text = text.lower()
    score = 0
    if text == "privacy policy" or text == "terms of service": score += 100
    elif text == "privacy" or text == "terms": score += 50
    if "/privacy" in href or "/legal/privacy" in href: score += 120
    if "/terms" in href or "/legal/terms" in href: score += 120
    if "privacy" in href: score += 20
    if "terms" in href: score += 20
    if "privacy" in text: score += 10
    if "terms" in text: score += 10
    if any(junk in href or junk in text for junk in ["blog", "advisor", "settings", "history", "search"]): score -= 50
    return score

def find_policy_links(base_url):
    """Finds policy links using a real browser (Selenium)."""
    if not (base_url.startswith('http://') or base_url.startswith('https://')):
        base_url = 'https://' + base_url
    
    domain = urlparse(base_url).netloc
    
    print("Initializing Selenium driver...")
    driver = get_selenium_driver()
    if driver is None:
        return []

    print(f"Scraping {base_url} with Selenium...")
    try:
        driver.get(base_url)
        # Give the page (and any JavaScript) 3 seconds to load
        time.sleep(3) 
        
        # Get the page's HTML *after* JavaScript has run
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        scored_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            text = a_tag.get_text(strip=True)
            
            if any(keyword in text.lower() for keyword in POLICY_KEYWORDS) or \
               any(keyword in href.lower() for keyword in POLICY_KEYWORDS):
                
                full_url = urljoin(base_url, href)
                
                if urlparse(full_url).netloc.endswith(domain):
                    score = score_link(href, text)
                    if score > 0:
                        scored_links.append((score, full_url))

        scored_links.sort(key=lambda x: x[0], reverse=True)
        
        final_links = []
        seen = set()
        for score, url in scored_links:
            if '#' in url and not url.startswith('#'):
                url = url.split('#')[0]
            if url not in seen:
                final_links.append(url)
                seen.add(url)
        
        if final_links:
            print(f"Found links via Selenium scrape: {final_links}")
            driver.quit()
            return final_links

    except Exception as e:
        print(f"Error scraping with Selenium: {e}")
    
    # --- PHASE 2: Guessing (Still useful) ---
    print(f"Scraping failed to find links. Moving to 'guessing' method.")
    
    common_paths = [
        'privacy', 'legal/privacy', 'privacy-policy', 
        'terms', 'legal/terms', 'terms-of-service',
        'cookie-policy', 'cookies'
    ]
    
    guessed_links = []
    clean_base_url = f"https://{domain}"

    for path in common_paths:
        guess_url = urljoin(clean_base_url, path)
        try:
            # We use Selenium to check the URL
            driver.get(guess_url)
            time.sleep(1) # Let it load/redirect
            final_url = driver.current_url
            
            # Check if it's on the same website and not a 404
            # (Note: This isn't a perfect 404 check, but it's good enough)
            if urlparse(final_url).netloc.endswith(domain) and "404" not in driver.title.lower():
                print(f"Guess successful: {final_url}")
                guessed_links.append(final_url)
        except Exception:
            pass # Ignore errors silently
    
    driver.quit() # Always close the browser
    
    # De-duplicate the results
    final_guessed = []
    seen_urls = set()
    for url in guessed_links:
        if url not in seen_urls:
            final_guessed.append(url)
            seen_urls.add(url)
    
    print(f"Found links via guessing: {final_guessed}")
    return final_guessed

def extract_text_from_url(url):
    """Extracts text from a URL using Selenium."""
    print(f"Extracting text from {url} with Selenium...")
    driver = get_selenium_driver()
    if driver is None:
        return None, "Error: Could not start Selenium driver."

    try:
        driver.get(url)
        time.sleep(2) # Give page time to load
        soup = BeautifulSoup(driver.page_source, 'lxml')
        driver.quit() # Close the browser
    except Exception as e:
        print(f"Error fetching {url} with Selenium: {e}")
        driver.quit()
        return None, f"Error: Could not fetch URL {url}"

    # --- (The rest of this function is the same as before) ---
    
    # Remove script, style, nav, footer, header, forms, and cookie banners
    for element in soup(["script", "style", "nav", "footer", "header", "form"]):
        element.decompose()
    
    main_content = soup.find('main')
    if not main_content:
        main_content = soup.find(role='main')
    if not main_content:
        main_content = soup.find('article')
    
    if not main_content:
        main_content = soup.body
        if not main_content:
            return None, "Could not find body of the page."

    text_tags = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
    
    text_chunks = []
    for tag in text_tags:
        text = tag.get_text(strip=True)
        if text and len(text.split()) > 4: 
            text_chunks.append(text)

    if not text_chunks:
        full_text = main_content.get_text(separator=' ', strip=True)
    else:
        full_text = ' '.join(text_chunks)

    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    if not full_text or len(full_text.split()) < 20:
        return full_text, "Warning: Extracted text is very short."

    return full_text, None