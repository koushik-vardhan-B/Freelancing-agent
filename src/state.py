"""
Agent State - TypedDict for LangGraph workflow

Defines the state that flows through all nodes in the workflow.
"""

from typing import TypedDict, List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class GigData:
    """Represents a scraped job/gig."""
    title: str
    company: str
    location: str
    job_type: str
    posted_date: str
    description: str
    job_url: str
    scraped_at: str = ""
    quality_score: int = 0
    ai_analysis: str = ""
    search_keyword: str = ""
    
    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AgentState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    
    Each node reads from and writes to this shared state.
    """
    # Configuration
    search_queries: List[str]          # Keywords to search for
    current_query_index: int           # Which keyword we're on
    max_pages_per_query: int           # Pages to scrape per keyword
    min_quality_score: int             # Minimum AI score to keep
    excel_path: str                    # Output file path
    
    # Processing State
    browser_ready: bool                # Is browser initialized?
    all_gigs: List[Dict]              # All scraped gigs
    filtered_gigs: List[Dict]         # Gigs that passed AI filter
    
    # Status
    errors: List[str]                  # Any errors encountered
    messages: List[str]               # Progress messages
    final_output: str                  # Final status message
    
    # Internal (set by workflow)
    step_count: int                    # How many steps executed


def create_initial_state(
    keywords: List[str],
    max_pages: int = 2,
    min_score: int = 5,
    excel_path: str = "output/freelance_gigs.xlsx"
) -> AgentState:
    """Create the initial state for the workflow."""
    return AgentState(
        search_queries=keywords,
        current_query_index=0,
        max_pages_per_query=max_pages,
        min_quality_score=min_score,
        excel_path=excel_path,
        browser_ready=False,
        all_gigs=[],
        filtered_gigs=[],
        errors=[],
        messages=[],
        final_output="",
        step_count=0
    )
