from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_url_content(url: str) -> str:
    """Uses a headless browser to render JavaScript and scrape full page text."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Set a 10s timeout so we don't hang the graph forever on slow sites
            page.goto(url, timeout=10000, wait_until="domcontentloaded")
            html = page.content()
            browser.close()
            
            # Parse and clean HTML
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts, styles, and navs
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
                
            text = soup.get_text(separator='\n')
            # Collapse extra whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)[:8000] # Cap at 8000 chars to avoid token bloat
    except Exception as e:
        print(f"Browser scraping failed for {url}: {e}")
        return ""
