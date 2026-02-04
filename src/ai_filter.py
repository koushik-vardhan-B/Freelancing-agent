"""
AI Filter - Uses Groq SDK to filter and score jobs

Analyzes job listings and identifies the best freelance opportunities.
"""

import json
from typing import List
from dataclasses import dataclass

from groq import Groq
from loguru import logger

from src.config import config
from src.linkedin_scraper import JobListing


SYSTEM_PROMPT = """You are a freelance job analyst. Analyze job listings and score them.

For each job, provide:
- quality_score (1-10): How good is this opportunity?
- reason: Brief explanation

Respond in JSON:
{
    "jobs": [
        {"index": 0, "quality_score": 8, "reason": "Good pay, clear scope"}
    ]
}

Only include jobs scoring 5 or higher."""


@dataclass
class FilteredJob:
    """A job that passed the AI filter."""
    job: JobListing
    quality_score: int
    reason: str


class AIFilter:
    """Uses Groq API to filter jobs."""
    
    def __init__(self):
        config.validate()
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def filter_jobs(self, jobs: List[JobListing], min_score: int = 5) -> List[FilteredJob]:
        """Filter jobs using AI."""
        if not jobs:
            return []
        
        logger.info(f"Filtering {len(jobs)} jobs with AI...")
        
        # Process in batches
        batch_size = 10
        filtered = []
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            results = self._filter_batch(batch, i, min_score)
            filtered.extend(results)
        
        logger.info(f"AI kept {len(filtered)} jobs (score >= {min_score})")
        return filtered
    
    def _filter_batch(self, jobs: List[JobListing], start_idx: int, min_score: int) -> List[FilteredJob]:
        """Filter a batch of jobs."""
        jobs_text = "\n".join([
            f"Job {start_idx + i}: {j.title} at {j.company} ({j.location})"
            for i, j in enumerate(jobs)
        ])
        
        prompt = f"Analyze these jobs:\n\n{jobs_text}\n\nOnly include jobs with score >= {min_score}."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            
            return self._parse_response(response.choices[0].message.content, jobs, start_idx, min_score)
            
        except Exception as e:
            logger.error(f"AI filter error: {e}")
            # On error, return all jobs with default score
            return [FilteredJob(job=j, quality_score=5, reason="Default") for j in jobs]
    
    def _parse_response(self, response: str, jobs: List[JobListing], start_idx: int, min_score: int) -> List[FilteredJob]:
        """Parse LLM response."""
        filtered = []
        
        try:
            # Clean response
            response = response.strip()
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            
            for result in data.get("jobs", []):
                idx = result.get("index", 0) - start_idx
                score = result.get("quality_score", 5)
                
                if 0 <= idx < len(jobs) and score >= min_score:
                    filtered.append(FilteredJob(
                        job=jobs[idx],
                        quality_score=score,
                        reason=result.get("reason", "")
                    ))
                    
        except json.JSONDecodeError:
            logger.warning("Could not parse AI response")
            return [FilteredJob(job=j, quality_score=5, reason="Parse error") for j in jobs]
        
        return filtered


def filter_jobs_with_ai(jobs: List[JobListing], min_score: int = 5) -> List[FilteredJob]:
    """Convenience function."""
    ai = AIFilter()
    return ai.filter_jobs(jobs, min_score)
