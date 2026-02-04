# LinkedIn Freelance Gigs Scraper

An AI-powered tool that scrapes freelance/contract jobs from LinkedIn and saves them to a formatted Excel file.

## Features

- **No LinkedIn Login Required** - Scrapes public job listings
- **AI-Powered Filtering** - Uses Groq AI to score and filter jobs (1-10)
- **Excel Export** - Formatted output with color-coded scores
- **Customizable** - Search any keywords, control pages scraped

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  LinkedIn        │────▶│   AI Filter      │────▶│   Excel Writer   │
│  Scraper         │     │   (Groq)         │     │   (openpyxl)     │
│  (Playwright)    │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Browser Automation | Playwright (sync API) |
| AI Filtering | Groq SDK (llama-3.3-70b) |
| Excel Output | openpyxl |
| Config | python-dotenv |
| Logging | loguru |

## Installation

```bash
# 1. Clone/download the project
cd "FreeLance agent"

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Set up environment
copy .env.example .env
# Edit .env and add your Groq API key
```

## Configuration

Create a `.env` file with:

```env
# Required for AI filtering (get from https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_api_key_here

# Optional
GROQ_MODEL=llama-3.3-70b-versatile
HEADLESS=true
MAX_PAGES=2
```

## Usage

### Basic Usage

```bash
python main.py
```

### Custom Search

```bash
# Custom keywords
python main.py --keywords "python developer freelance"

# Multiple pages (25 jobs per page)
python main.py --keywords "react developer" --pages 3

# Skip AI filtering (faster)
python main.py --keywords "python" --no-filter

# Show browser window
python main.py --keywords "python" --visible

# Custom output file
python main.py --output my_jobs.xlsx
```

### All Options

```
python main.py --help

Options:
  -k, --keywords    Search keywords (default: "freelance developer")
  -p, --pages       Pages to scrape, 25 jobs each (default: 2)
  -o, --output      Output Excel file (default: output/freelance_gigs.xlsx)
  --min-score       Minimum AI quality score (default: 5)
  --no-filter       Skip AI filtering
  --visible         Show browser window
```

## Output

Creates an Excel file with:

| Column | Description |
|--------|-------------|
| Title | Job title |
| Company | Company name |
| Location | Job location |
| Type | Contract/Freelance |
| Posted | When posted |
| AI Score | Quality score (1-10) |
| AI Analysis | Why this score |
| Job URL | Link to apply |
| Scraped At | When scraped |

AI scores are color-coded:
- 🟢 Green: 8-10 (excellent)
- 🟡 Yellow: 6-7 (good)
- 🔴 Red: 1-5 (poor)

## Project Structure

```
FreeLance agent/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── .env                   # Your config (not in git)
├── output/                # Excel files saved here
│   └── freelance_gigs.xlsx
└── src/
    ├── __init__.py
    ├── config.py          # Configuration loader
    ├── linkedin_scraper.py # Playwright scraper
    ├── ai_filter.py       # Groq AI filter
    └── excel_writer.py    # Excel output
```

## How It Works

1. **Scraping**: Uses Playwright to load LinkedIn's public job search page, scrolls to load jobs, and extracts job cards (title, company, location, URL, etc.)

2. **AI Filtering**: Sends batches of jobs to Groq's LLM which scores each job 1-10 based on quality, clarity, and freelance fit

3. **Excel Export**: Writes filtered jobs to a formatted Excel file with color-coded scores and frozen headers

## Troubleshooting

### Playwright not working
```bash
playwright install chromium
```

### No module found errors
```bash
pip install -r requirements.txt
```

### AI filter not working
- Make sure `GROQ_API_KEY` is set in `.env`
- Get a free key from https://console.groq.com/keys

### Timeout errors
LinkedIn may be slow. Try:
- Using `--visible` to see what's happening
- Reducing pages with `--pages 1`

## License

MIT
