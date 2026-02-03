# Freelance Job Discovery Agent

An AI-powered agent that autonomously discovers, filters, and ranks freelance job opportunities from public sources based on your skills and preferences.

## Features

- 🤖 **Autonomous Job Discovery** - Agent searches multiple job sources automatically
- 🎯 **Skill-Based Filtering** - Matches jobs to your specific skill set
- 📊 **Intelligent Ranking** - LLM-powered relevance scoring
- 💾 **Persistent Storage** - ChromaDB for job and profile storage
- ⚡ **Fast API** - RESTful endpoints for easy integration

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangChain + LangGraph |
| Backend API | FastAPI |
| Vector Database | ChromaDB |
| LLM Provider | Groq Cloud (Free Tier) |
| Embeddings | HuggingFace sentence-transformers |

## Project Structure

```
src/
├── config.py           # Configuration and environment settings
├── models/             # Pydantic schemas and state definitions
├── llm/                # LLM and embeddings setup
├── db/                 # ChromaDB vector store
├── scrapers/           # Job source scrapers
├── agent/              # LangGraph workflow
└── api/                # FastAPI routes
```

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Server

```bash
uvicorn src.api.main:app --reload
```

### 4. Test the API

```bash
# Create a user profile
curl -X POST http://localhost:8000/users/profile \
  -H "Content-Type: application/json" \
  -d '{"name": "Developer", "skills": ["Python", "FastAPI"]}'

# Search for jobs
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"user_id": "your-user-id", "keywords": ["python developer"]}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/profile` | Create/update user profile |
| GET | `/users/profile/{id}` | Get user profile |
| POST | `/agent/run` | Start job discovery agent |
| GET | `/agent/status/{id}` | Check agent run status |
| GET | `/jobs/saved` | List saved jobs |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq Cloud API key | Yes |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | No |

## License

MIT
