# LinkedIn Freelance Gigs Scraper

AI-powered agent that scrapes LinkedIn for freelance gigs and saves to Excel.

## Architecture

Uses **LangGraph** workflow with 3 nodes:

```
┌─────────┐     ┌────────┐     ┌────────┐
│ SCRAPE  │────▶│ FILTER │────▶│  SAVE  │────▶ END
└────┬────┘     └────────┘     └────────┘
     │                              
     └──────────────────────┐
               (loop back)  │
                           ▼
```

- **Scrape Node**: Uses Playwright to scrape LinkedIn (no login required)
- **Filter Node**: Uses Groq AI to score job quality (1-10)
- **Save Node**: Writes to formatted Excel file

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt
playwright install chromium

# 2. Set API key (optional, for AI filtering)
echo "GROQ_API_KEY=gsk_xxx" > .env

# 3. Run
python main.py --keywords "python developer" "fastapi freelance"
```

## Usage

```bash
# Single keyword
python main.py --keywords "freelance developer"

# Multiple keywords
python main.py -k "python developer" "react freelance" "contract engineer"

# More pages per keyword
python main.py -k "python" --pages 3

# Skip AI filtering (faster)
python main.py -k "python" --no-filter

# Custom output file
python main.py -k "python" --output jobs.xlsx
```

## Output

Creates Excel file with columns:
- Title, Company, Location, Type
- Posted, Score, AI Analysis
- Job URL, Scraped At

## Project Structure

```
src/
├── config.py           # Settings
├── state.py            # LangGraph AgentState
├── workflow.py         # LangGraph nodes & graph
├── linkedin_scraper.py # Playwright scraper
├── ai_filter.py        # Groq AI filter
└── excel_writer.py     # Excel output
```
