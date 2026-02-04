"""
LinkedIn Job Scraper - Using Playwright

Scrapes freelance/contract jobs from LinkedIn's public job search.
No login required - uses public job listings.
"""

import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from playwright.async_api import async_playwright, Page, Browser, Playwright
from loguru import logger


@dataclass
class JobListing:
    """Represents a single job listing."""
    title: str
    company: str
    location: str
    job_type: str  # Full-time, Contract, Freelance, etc.
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
    """
    Scrapes LinkedIn jobs without requiring login.
    Uses the public job search page.
    """
    
    BASE_URL = "https://www.linkedin.com/jobs/search"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def start(self):
        """Start the browser."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
        # Set user agent to look like a real browser
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
    
    async def stop(self):
        """Stop the browser properly."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    def _build_search_url(
        self,
        keywords: str,
        location: str = "",
        job_type: str = "C",  # C = Contract, F = Full-time
        page: int = 0
    ) -> str:
        """
        Build LinkedIn job search URL.
        
        Args:
            keywords: Search keywords
            location: Location filter
            job_type: F=Full-time, P=Part-time, C=Contract, T=Temporary, I=Internship
            page: Page number (0-indexed, 25 jobs per page)
        """
        params = [
            f"keywords={keywords.replace(' ', '%20')}",
            f"location={location.replace(' ', '%20')}" if location else "",
            f"f_JT={job_type}" if job_type else "",
            f"start={page * 25}" if page > 0 else "",
            "sortBy=DD",  # Sort by date (most recent)
        ]
        
        query = "&".join([p for p in params if p])
        return f"{self.BASE_URL}?{query}"
    
    async def scrape_jobs(
        self,
        keywords: str,
        location: str = "",
        max_pages: int = 3,
        delay: float = 2.0
    ) -> List[JobListing]:
        """
        Scrape jobs from LinkedIn.
        
        Args:
            keywords: Search keywords (e.g., "python developer freelance")
            location: Location filter (e.g., "United States")
            max_pages: Maximum pages to scrape (25 jobs per page)
            delay: Delay between page loads (seconds)
            
        Returns:
            List of JobListing objects
        """
        all_jobs = []
        
        for page_num in range(max_pages):
            logger.info(f"Scraping page {page_num + 1}/{max_pages}...")
            
            # Build URL for contract/freelance jobs
            url = self._build_search_url(keywords, location, job_type="C", page=page_num)
            
            try:
                jobs = await self._scrape_page(url)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs on page {page_num + 1}")
                
                if len(jobs) == 0:
                    logger.info("No more jobs found, stopping.")
                    break
                
                # Delay between pages to avoid rate limiting
                if page_num < max_pages - 1:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error scraping page {page_num + 1}: {e}")
                continue
        
        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        return all_jobs
    
    async def _scrape_page(self, url: str) -> List[JobListing]:
        """Scrape a single page of job listings."""
        jobs = []
        
        await self.page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait for job cards to load
        try:
            await self.page.wait_for_selector(".jobs-search__results-list", timeout=10000)
        except:
            logger.warning("Job list not found, page might be different or blocked")
            return jobs
        
        # Scroll to load more jobs
        await self._scroll_page()
        
        # Get all job cards
        job_cards = await self.page.query_selector_all(".jobs-search__results-list > li")
        
        for card in job_cards:
            try:
                job = await self._parse_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error parsing job card: {e}")
                continue
        
        return jobs
    
    async def _scroll_page(self):
        """Scroll down to load all jobs on the page."""
        for _ in range(3):
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(0.5)
    
    async def _parse_job_card(self, card) -> Optional[JobListing]:
        """Parse a single job card element."""
        
        # Title
        title_elem = await card.query_selector(".base-search-card__title")
        title = await title_elem.inner_text() if title_elem else "N/A"
        
        # Company
        company_elem = await card.query_selector(".base-search-card__subtitle")
        company = await company_elem.inner_text() if company_elem else "N/A"
        
        # Location
        location_elem = await card.query_selector(".job-search-card__location")
        location = await location_elem.inner_text() if location_elem else "N/A"
        
        # Posted date
        date_elem = await card.query_selector("time")
        posted_date = await date_elem.get_attribute("datetime") if date_elem else "N/A"
        if posted_date and posted_date != "N/A":
            try:
                posted_date = datetime.fromisoformat(posted_date.replace("Z", "")).strftime("%Y-%m-%d")
            except:
                pass
        
        # Job URL
        link_elem = await card.query_selector("a.base-card__full-link")
        job_url = await link_elem.get_attribute("href") if link_elem else "N/A"
        
        # Clean up job URL (remove tracking params)
        if job_url and "?" in job_url:
            job_url = job_url.split("?")[0]
        
        return JobListing(
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            job_type="Contract/Freelance",
            posted_date=posted_date,
            description="",  # Will be filled by detail scraping if needed
            job_url=job_url
        )
    
    async def get_job_details(self, job: JobListing) -> JobListing:
        """
        Get full job description by visiting the job page.
        
        Note: This is slower but gives complete info.
        """
        if not job.job_url or job.job_url == "N/A":
            return job
        
        try:
            await self.page.goto(job.job_url, wait_until="networkidle", timeout=20000)
            
            # Wait for description to load
            await self.page.wait_for_selector(".description__text", timeout=5000)
            
            # Get description
            desc_elem = await self.page.query_selector(".description__text")
            if desc_elem:
                job.description = await desc_elem.inner_text()
                job.description = job.description.strip()[:2000]  # Limit length
            
        except Exception as e:
            logger.debug(f"Could not get details for {job.title}: {e}")
        
        return job


async def scrape_linkedin_jobs(
    keywords: str,
    location: str = "",
    max_pages: int = 3,
    headless: bool = True,
    get_details: bool = False
) -> List[JobListing]:
    """
    Main function to scrape LinkedIn jobs.
    
    Args:
        keywords: Search keywords
        location: Location filter
        max_pages: Max pages to scrape
        headless: Run browser in background
        get_details: Whether to fetch full job descriptions (slower)
        
    Returns:
        List of JobListing objects
    """
    scraper = LinkedInScraper(headless=headless)
    
    try:
        await scraper.start()
        jobs = await scraper.scrape_jobs(keywords, location, max_pages)
        
        # Optionally get full descriptions
        if get_details:
            logger.info("Fetching job details...")
            for i, job in enumerate(jobs):
                logger.info(f"Getting details {i+1}/{len(jobs)}: {job.title}")
                jobs[i] = await scraper.get_job_details(job)
                await asyncio.sleep(1)  # Be nice to LinkedIn
        
        return jobs
    finally:
        await scraper.stop()


# Convenience function for sync usage
def scrape_jobs(keywords: str, location: str = "", max_pages: int = 3) -> List[JobListing]:
    """Synchronous wrapper for scrape_linkedin_jobs."""
    return asyncio.run(scrape_linkedin_jobs(keywords, location, max_pages))


if __name__ == "__main__":
    # Test the scraper
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    jobs = scrape_jobs("python developer freelance", max_pages=1)
    for job in jobs[:5]:
        print(f"\n{job.title} @ {job.company}")
        print(f"  Location: {job.location}")
        print(f"  Posted: {job.posted_date}")
        print(f"  URL: {job.job_url}")
