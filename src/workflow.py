"""
LangGraph Workflow - Orchestrates the scraping pipeline

Workflow: scrape → filter → save → END
         ↑______|  (loops for each keyword)
"""

import asyncio
from typing import Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from loguru import logger

from src.state import AgentState, create_initial_state
from src.linkedin_scraper import scrape_linkedin_jobs, JobListing
from src.ai_filter import filter_jobs_with_ai, FilteredJob
from src.excel_writer import write_to_excel
from src.config import config


# ============================================
# WORKFLOW NODES
# ============================================

async def scrape_node(state: AgentState) -> AgentState:
    """
    Node: Scrape LinkedIn jobs for current keyword.
    
    Reads: search_queries, current_query_index, max_pages_per_query
    Writes: all_gigs, current_query_index, messages
    """
    current_idx = state["current_query_index"]
    queries = state["search_queries"]
    
    if current_idx >= len(queries):
        state["messages"].append("All keywords scraped")
        return state
    
    keyword = queries[current_idx]
    max_pages = state["max_pages_per_query"]
    
    logger.info(f"[{current_idx + 1}/{len(queries)}] Scraping: {keyword}")
    state["messages"].append(f"Scraping: {keyword}")
    
    try:
        # Use our simple scraper (no login)
        jobs = await scrape_linkedin_jobs(
            keywords=keyword,
            max_pages=max_pages,
            headless=True
        )
        
        # Convert to dicts and add keyword
        for job in jobs:
            gig_dict = job.to_dict()
            gig_dict["search_keyword"] = keyword
            state["all_gigs"].append(gig_dict)
        
        state["messages"].append(f"Found {len(jobs)} jobs for '{keyword}'")
        logger.info(f"Found {len(jobs)} jobs for '{keyword}'")
        
    except Exception as e:
        error_msg = f"Error scraping '{keyword}': {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
    
    # Move to next keyword
    state["current_query_index"] = current_idx + 1
    state["step_count"] = state.get("step_count", 0) + 1
    
    return state


def filter_node(state: AgentState) -> AgentState:
    """
    Node: Filter jobs using AI.
    
    Reads: all_gigs, min_quality_score
    Writes: filtered_gigs, messages
    """
    all_gigs = state["all_gigs"]
    min_score = state["min_quality_score"]
    
    if not all_gigs:
        state["messages"].append("No gigs to filter")
        return state
    
    logger.info(f"Filtering {len(all_gigs)} gigs with AI...")
    state["messages"].append(f"AI filtering {len(all_gigs)} gigs...")
    
    try:
        # Validate API key
        config.validate()
        
        # Convert dicts back to JobListing objects
        from src.linkedin_scraper import JobListing
        job_listings = []
        for gig in all_gigs:
            job_listings.append(JobListing(
                title=gig.get("title", ""),
                company=gig.get("company", ""),
                location=gig.get("location", ""),
                job_type=gig.get("job_type", ""),
                posted_date=gig.get("posted_date", ""),
                description=gig.get("description", ""),
                job_url=gig.get("job_url", ""),
                scraped_at=gig.get("scraped_at", "")
            ))
        
        # Filter with AI
        filtered = filter_jobs_with_ai(job_listings, min_score=min_score)
        
        # Convert back to dicts with AI info
        for f_job in filtered:
            gig_dict = f_job.job.to_dict()
            gig_dict["quality_score"] = f_job.quality_score
            gig_dict["ai_analysis"] = f_job.reason
            state["filtered_gigs"].append(gig_dict)
        
        state["messages"].append(f"AI kept {len(filtered)} quality gigs")
        logger.info(f"AI filter kept {len(filtered)} gigs")
        
    except ValueError as e:
        # No API key - skip filtering, keep all
        logger.warning(f"AI filter skipped: {e}")
        state["messages"].append("AI filter skipped (no API key)")
        state["filtered_gigs"] = all_gigs
        
    except Exception as e:
        error_msg = f"AI filter error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(error_msg)
        # On error, keep all gigs
        state["filtered_gigs"] = all_gigs
    
    state["step_count"] = state.get("step_count", 0) + 1
    return state


def save_node(state: AgentState) -> AgentState:
    """
    Node: Save filtered gigs to Excel.
    
    Reads: filtered_gigs, excel_path
    Writes: final_output, messages
    """
    gigs = state["filtered_gigs"]
    excel_path = state["excel_path"]
    
    if not gigs:
        state["final_output"] = "No gigs to save"
        state["messages"].append("No gigs to save")
        return state
    
    logger.info(f"Saving {len(gigs)} gigs to Excel...")
    
    try:
        # Convert to format expected by excel_writer
        from src.linkedin_scraper import JobListing
        from src.ai_filter import FilteredJob
        
        filtered_jobs = []
        for gig in gigs:
            job = JobListing(
                title=gig.get("title", ""),
                company=gig.get("company", ""),
                location=gig.get("location", ""),
                job_type=gig.get("job_type", ""),
                posted_date=gig.get("posted_date", ""),
                description=gig.get("description", ""),
                job_url=gig.get("job_url", ""),
                scraped_at=gig.get("scraped_at", "")
            )
            filtered_jobs.append(FilteredJob(
                job=job,
                quality_score=gig.get("quality_score", 5),
                reason=gig.get("ai_analysis", ""),
                is_freelance=True,
                is_legitimate=True
            ))
        
        output_path = write_to_excel(filtered_jobs, excel_path)
        
        state["final_output"] = f"SUCCESS: Saved {len(gigs)} gigs to {output_path}"
        state["messages"].append(f"Saved to {output_path}")
        logger.info(f"Saved to {output_path}")
        
    except Exception as e:
        error_msg = f"Excel save error: {str(e)}"
        state["errors"].append(error_msg)
        state["final_output"] = f"ERROR: {error_msg}"
        logger.error(error_msg)
    
    state["step_count"] = state.get("step_count", 0) + 1
    return state


# ============================================
# CONDITIONAL EDGES
# ============================================

def should_continue_scraping(state: AgentState) -> Literal["scrape", "filter"]:
    """Decide whether to scrape more keywords or move to filtering."""
    current_idx = state["current_query_index"]
    total_queries = len(state["search_queries"])
    
    if current_idx < total_queries:
        return "scrape"  # More keywords to scrape
    return "filter"      # Done scraping, move to filter


# ============================================
# BUILD WORKFLOW
# ============================================

def create_workflow():
    """
    Create and compile the LangGraph workflow.
    
    Flow:
        scrape ──┬──▶ scrape (loop until all keywords done)
                 │
                 └──▶ filter ──▶ save ──▶ END
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("scrape", scrape_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("save", save_node)
    
    # Set entry point
    workflow.set_entry_point("scrape")
    
    # Add conditional edge from scrape
    workflow.add_conditional_edges(
        "scrape",
        should_continue_scraping,
        {
            "scrape": "scrape",  # Loop back
            "filter": "filter"   # Move to filter
        }
    )
    
    # Linear edges
    workflow.add_edge("filter", "save")
    workflow.add_edge("save", END)
    
    # Compile
    return workflow.compile()


# ============================================
# RUN WORKFLOW
# ============================================

async def run_workflow(
    keywords: list[str],
    max_pages: int = 2,
    min_score: int = 5,
    excel_path: str = "output/freelance_gigs.xlsx"
) -> AgentState:
    """
    Run the complete scraping workflow.
    
    Args:
        keywords: List of search keywords
        max_pages: Pages per keyword
        min_score: Minimum AI quality score
        excel_path: Output file path
        
    Returns:
        Final AgentState with results
    """
    # Create initial state
    initial_state = create_initial_state(
        keywords=keywords,
        max_pages=max_pages,
        min_score=min_score,
        excel_path=excel_path
    )
    
    # Create and run workflow
    app = create_workflow()
    
    # LangGraph invoke (with async support)
    # Note: LangGraph nodes are sync by default, but we made scrape async
    # So we need to handle this
    
    final_state = await run_async_workflow(app, initial_state)
    
    return final_state


async def run_async_workflow(app, state: AgentState) -> AgentState:
    """
    Run workflow with async node support.
    
    Since our scrape_node is async, we run it manually.
    """
    current_state = state.copy()
    
    # Phase 1: Scrape all keywords
    while current_state["current_query_index"] < len(current_state["search_queries"]):
        current_state = await scrape_node(current_state)
        await asyncio.sleep(1)  # Brief delay between keywords
    
    # Phase 2: Filter
    current_state = filter_node(current_state)
    
    # Phase 3: Save
    current_state = save_node(current_state)
    
    return current_state
