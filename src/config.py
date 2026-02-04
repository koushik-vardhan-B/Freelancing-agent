"""
Configuration - Loads settings from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Groq (AI filtering)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Scraping
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "2"))
    
    # Output
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    
    def validate(self):
        """Validate required settings."""
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env file")


config = Config()
