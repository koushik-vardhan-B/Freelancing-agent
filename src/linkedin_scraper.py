"""
LinkedIn Job Scraper - Sync Playwright Version

Scrapes freelance/contract jobs from LinkedIn's public job search.
No login required - uses public job listings.
"""

from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import time

from playwright.sync_api import sync_playwright, Page, Browser
from loguru import logger


@dataclass
class JobListing:
    """Represents a single job listing."""
    title: str
    company: str
    location: str
    job_type: str
    posted_date: str
    description: str
    job_url: str
    scraped_at: str = ""
    
    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LinkedInScraper:
    """Scrapes LinkedIn jobs using sync Playwright (no async issues on Windows)."""
    
    BASE_URL = "https://www.linkedin.com/jobs/search"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    def start(self):
        """Start the browser."""
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        
        # Set user agent
        self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def stop(self):
        """Stop the browser."""
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
        """Build LinkedIn job search URL."""
        params = [
            f"keywords={keywords.replace(' ', '%20')}",
            f"location={location.replace(' ', '%20')}" if location else "",
            "f_JT=C",  # Contract jobs
            f"start={page * 25}" if page > 0 else "",
            "sortBy=DD",  # Sort by date
        ]
        query = "&".join([p for p in params if p])
        return f"{self.BASE_URL}?{query}"
    
    def scrape_jobs(
        self,
        keywords: str,
        location: str = "",
        max_pages: int = 2,
        delay: float = 2.0
    ) -> List[JobListing]:
        """Scrape jobs from LinkedIn."""
        all_jobs = []
        
        for page_num in range(max_pages):
            logger.info(f"Scraping page {page_num + 1}/{max_pages}...")
            
            url = self._build_search_url(keywords, location, page=page_num)
            
            try:
                jobs = self._scrape_page(url)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs on page {page_num + 1}")
                
                if len(jobs) == 0:
                    break
                
                if page_num < max_pages - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error scraping page {page_num + 1}: {e}")
                continue
        
        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        return all_jobs
    
    def _scrape_page(self, url: str) -> List[JobListing]:
        """Scrape a single page."""
        jobs = []
        
        self.page.goto(url, wait_until="networkidle", timeout=30000)
        
        try:
            self.page.wait_for_selector(".jobs-search__results-list", timeout=10000)
        except:
            logger.warning("Job list not found")
            return jobs
        
        # Scroll to load more
        for _ in range(3):
            self.page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(0.5)
        
        # Get job cards
        job_cards = self.page.query_selector_all(".jobs-search__results-list > li")
        
        for card in job_cards:
            try:
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                continue
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[JobListing]:
        """Parse a job card."""
        title_elem = card.query_selector(".base-search-card__title")
        title = title_elem.inner_text() if title_elem else "N/A"
        
        company_elem = card.query_selector(".base-search-card__subtitle")
        company = company_elem.inner_text() if company_elem else "N/A"
        
        location_elem = card.query_selector(".job-search-card__location")
        location = location_elem.inner_text() if location_elem else "N/A"
        
        date_elem = card.query_selector("time")
        posted_date = date_elem.get_attribute("datetime") if date_elem else "N/A"
        
        link_elem = card.query_selector("a.base-card__full-link")
        job_url = link_elem.get_attribute("href") if link_elem else "N/A"
        if job_url and "?" in job_url:
            job_url = job_url.split("?")[0]
        
        return JobListing(
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            job_type="Contract/Freelance",
            posted_date=posted_date,
            description="",
            job_url=job_url
        )


def scrape_linkedin_jobs(
    keywords: str,
    location: str = "",
    max_pages: int = 2,
    headless: bool = True
) -> List[JobListing]:
    """Main function to scrape LinkedIn jobs."""
    scraper = LinkedInScraper(headless=headless)
    
    try:
        scraper.start()
        jobs = scraper.scrape_jobs(keywords, location, max_pages)
        return jobs
    finally:
        scraper.stop()


if __name__ == "__main__":
    # Quick test
    jobs = scrape_linkedin_jobs("python developer freelance", max_pages=1)
    for job in jobs[:5]:
        print(f"{job.title} @ {job.company}")
