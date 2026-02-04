"""
AI Filter - Uses Groq SDK directly to filter and score jobs

Analyzes job listings and identifies the best freelance opportunities.
Uses the groq SDK directly (no langchain dependency issues).
"""

import json
from typing import List
from dataclasses import dataclass

from groq import Groq
from loguru import logger

from src.config import config
from src.linkedin_scraper import JobListing


SYSTEM_PROMPT = """You are an expert freelance job analyst. Analyze job listings and determine if they are good freelance/contract opportunities.

For each job, evaluate:
1. Is it truly a freelance/contract role (not full-time)?
2. Does it seem legitimate (not a scam)?
3. Quality of the opportunity

Respond in JSON format:
{
    "jobs": [
        {
            "index": 0,
            "is_freelance": true,
            "is_legitimate": true,
            "quality_score": 8,
            "reason": "Clear project scope, reputable company"
        }
    ]
}

Quality score is 1-10:
- 1-3: Poor (vague, low pay, red flags)
- 4-6: Average  
- 7-10: Excellent (clear scope, good pay)

Only include jobs scoring 5 or higher."""


@dataclass
class FilteredJob:
    """A job that passed the AI filter."""
    job: JobListing
    quality_score: int
    reason: str
    is_freelance: bool
    is_legitimate: bool


class AIFilter:
    """Uses Groq API directly to filter jobs."""
    
    def __init__(self):
        config.validate()
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def filter_jobs(self, jobs: List[JobListing], min_score: int = 5) -> List[FilteredJob]:
        """
        Filter jobs using AI.
        
        Args:
            jobs: List of scraped jobs
            min_score: Minimum quality score (1-10)
            
        Returns:
            List of FilteredJob objects that passed the filter
        """
        if not jobs:
            return []
        
        logger.info(f"Filtering {len(jobs)} jobs with AI...")
        
        # Process in batches
        batch_size = 10
        filtered_jobs = []
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_results = self._filter_batch(batch, i, min_score)
            filtered_jobs.extend(batch_results)
        
        logger.info(f"AI filter kept {len(filtered_jobs)} jobs (score >= {min_score})")
        return filtered_jobs
    
    def _filter_batch(self, jobs: List[JobListing], start_index: int, min_score: int) -> List[FilteredJob]:
        """Filter a batch of jobs."""
        
        jobs_text = self._format_jobs(jobs, start_index)
        
        prompt = f"""Analyze these job listings:

{jobs_text}

Only include jobs with quality score >= {min_score}.
Respond ONLY with valid JSON, no other text."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content, jobs, start_index, min_score)
            
        except Exception as e:
            logger.error(f"AI filter error: {e}")
            # On error, return all jobs with default score
            return [
                FilteredJob(
                    job=job,
                    quality_score=5,
                    reason="Could not analyze - included by default",
                    is_freelance=True,
                    is_legitimate=True
                )
                for job in jobs
            ]
    
    def _format_jobs(self, jobs: List[JobListing], start_index: int) -> str:
        """Format jobs for the prompt."""
        lines = []
        for i, job in enumerate(jobs):
            idx = start_index + i
            desc = job.description[:300] if job.description else 'N/A'
            lines.append(f"""
Job {idx}:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Type: {job.job_type}
- Posted: {job.posted_date}
- Description: {desc}
""")
        return "\n".join(lines)
    
    def _parse_response(self, response: str, jobs: List[JobListing], start_index: int, min_score: int) -> List[FilteredJob]:
        """Parse LLM response."""
        filtered = []
        
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            job_results = data.get("jobs", [])
            
            for result in job_results:
                idx = result.get("index", 0)
                local_idx = idx - start_index
                score = result.get("quality_score", 5)
                
                if 0 <= local_idx < len(jobs) and score >= min_score:
                    filtered.append(FilteredJob(
                        job=jobs[local_idx],
                        quality_score=score,
                        reason=result.get("reason", ""),
                        is_freelance=result.get("is_freelance", True),
                        is_legitimate=result.get("is_legitimate", True)
                    ))
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse AI response: {e}")
            # Return all jobs with default scores
            for job in jobs:
                filtered.append(FilteredJob(
                    job=job,
                    quality_score=5,
                    reason="Parse error - included by default",
                    is_freelance=True,
                    is_legitimate=True
                ))
        
        return filtered


def filter_jobs_with_ai(jobs: List[JobListing], min_score: int = 5) -> List[FilteredJob]:
    """Convenience function to filter jobs."""
    ai_filter = AIFilter()
    return ai_filter.filter_jobs(jobs, min_score)
