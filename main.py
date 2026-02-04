# =============================================================================
# WINDOWS EVENT LOOP FIX - MUST BE AT THE VERY TOP
# =============================================================================
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =============================================================================
# Now safe to import everything else
# =============================================================================

"""
LinkedIn Freelance Gigs Scraper - Main Entry Point

Uses LangGraph workflow: scrape → filter → save
"""

import argparse
from pathlib import Path
from datetime import datetime

from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape freelance gigs from LinkedIn using LangGraph workflow"
    )
    
    parser.add_argument(
        "--keywords", "-k",
        type=str,
        nargs="+",
        default=["freelance developer"],
        help="Search keywords (can specify multiple)"
    )
    
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=2,
        help="Number of pages to scrape per keyword (default: 2)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output/freelance_gigs.xlsx",
        help="Output Excel file path"
    )
    
    parser.add_argument(
        "--min-score",
        type=int,
        default=5,
        help="Minimum AI quality score (1-10, default: 5)"
    )
    
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip AI filtering"
    )
    
    return parser.parse_args()


async def main():
    """Main function - runs the LangGraph workflow."""
    args = parse_args()
    
    # Import here to avoid loading heavy modules when showing help
    from src.workflow import run_workflow
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Header
    print("\n" + "=" * 60)
    print("🔍 LinkedIn Freelance Gigs Scraper (LangGraph)")
    print("=" * 60)
    print(f"Keywords: {', '.join(args.keywords)}")
    print(f"Pages per keyword: {args.pages}")
    print(f"Min AI Score: {args.min_score if not args.no_filter else 'Disabled'}")
    print(f"Output: {args.output}")
    print("=" * 60 + "\n")
    
    # Run workflow
    min_score = 0 if args.no_filter else args.min_score
    
    final_state = await run_workflow(
        keywords=args.keywords,
        max_pages=args.pages,
        min_score=min_score,
        excel_path=args.output
    )
    
    # Results
    print("\n" + "=" * 60)
    print("📊 WORKFLOW COMPLETE")
    print("=" * 60)
    
    # Messages
    if final_state.get("messages"):
        print("\nProgress:")
        for msg in final_state["messages"]:
            print(f"  ✓ {msg}")
    
    # Errors
    if final_state.get("errors"):
        print("\n⚠️ Errors:")
        for err in final_state["errors"]:
            print(f"  ✗ {err}")
    
    # Final output
    print(f"\n{final_state.get('final_output', 'No output')}")
    
    # Stats
    print(f"\nStats:")
    print(f"  Total scraped: {len(final_state.get('all_gigs', []))} gigs")
    print(f"  After filter: {len(final_state.get('filtered_gigs', []))} gigs")
    print(f"  Steps executed: {final_state.get('step_count', 0)}")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
