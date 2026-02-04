"""
LinkedIn Freelance Gigs Scraper - Main Entry Point

Simple workflow: scrape -> filter -> save to Excel

Usage:
    python main.py                                    # Defaults
    python main.py --keywords "python developer"     # Custom keywords
    python main.py --no-filter                       # Skip AI
"""

import argparse
import sys
from pathlib import Path

from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape LinkedIn freelance gigs")
    
    parser.add_argument(
        "--keywords", "-k",
        type=str,
        default="freelance developer",
        help="Search keywords"
    )
    
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=2,
        help="Pages to scrape (25 jobs each)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output/freelance_gigs.xlsx",
        help="Output Excel file"
    )
    
    parser.add_argument(
        "--min-score",
        type=int,
        default=5,
        help="Min AI quality score (1-10)"
    )
    
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip AI filtering"
    )
    
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Show browser window"
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Imports
    from src.linkedin_scraper import scrape_linkedin_jobs
    from src.ai_filter import filter_jobs_with_ai, FilteredJob
    from src.excel_writer import write_to_excel
    from src.config import config
    
    # Ensure output dir exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Header
    print("\n" + "=" * 50)
    print("LinkedIn Freelance Gigs Scraper")
    print("=" * 50)
    print(f"Keywords: {args.keywords}")
    print(f"Pages: {args.pages}")
    print(f"AI Filter: {'Disabled' if args.no_filter else f'Min score {args.min_score}'}")
    print(f"Output: {args.output}")
    print("=" * 50 + "\n")
    
    # Step 1: Scrape
    logger.info("Starting LinkedIn scraper...")
    jobs = scrape_linkedin_jobs(
        keywords=args.keywords,
        max_pages=args.pages,
        headless=not args.visible
    )
    
    if not jobs:
        logger.error("No jobs found!")
        return
    
    logger.info(f"Scraped {len(jobs)} jobs")
    
    # Step 2: Filter (optional)
    if args.no_filter:
        # Convert to FilteredJob format for Excel
        filtered = [FilteredJob(job=j, quality_score=0, reason="Not analyzed") for j in jobs]
    else:
        try:
            config.validate()
            filtered = filter_jobs_with_ai(jobs, min_score=args.min_score)
        except ValueError as e:
            logger.warning(f"AI filter skipped: {e}")
            filtered = [FilteredJob(job=j, quality_score=0, reason="No API key") for j in jobs]
    
    logger.info(f"After filter: {len(filtered)} jobs")
    
    # Step 3: Save to Excel
    output_path = write_to_excel(filtered, args.output)
    
    # Summary
    print("\n" + "=" * 50)
    print("DONE!")
    print("=" * 50)
    print(f"Scraped: {len(jobs)} jobs")
    print(f"Filtered: {len(filtered)} jobs")
    print(f"Saved to: {output_path}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
