"""
Configuration - Simple settings loader
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Simple configuration class."""
    
    # Groq API Key (required)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # LinkedIn Search Settings
    DEFAULT_KEYWORDS: list = ["freelance", "contract", "remote"]
    DEFAULT_LOCATION: str = "United States"
    MAX_PAGES: int = 5
    
    # Output Settings
    OUTPUT_DIR: Path = Path("output")
    OUTPUT_FILE: str = "freelance_gigs.xlsx"
    
    # Scraping Settings
    HEADLESS: bool = True  # Run browser in background
    DELAY_BETWEEN_PAGES: float = 2.0  # Seconds between page loads
    
    @classmethod
    def validate(cls):
        """Check required settings."""
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is required!\n"
                "Get your free key from: https://console.groq.com/keys\n"
                "Then add it to your .env file"
            )
        
        # Create output directory
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_output_path(cls) -> Path:
        """Get full path to output Excel file."""
        return cls.OUTPUT_DIR / cls.OUTPUT_FILE


config = Config()
