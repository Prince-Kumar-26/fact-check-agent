# 📦 Project Dependencies & Environment Variables

This document lists all the third-party services, API keys, and Python/Node packages required to run the Fact-Check Agent.

## Environment Variables (`.env`)

To run the backend, you must create a `.env` file in the root directory.

| Variable Name | Required? | Purpose |
|--------------|-----------|---------|
| `GROQ_API_KEY` | **Yes** | Used to access ultra-fast LLMs (like `llama-3.3-70b` or `gpt-oss-120b`) for the Agents and Judge. |
| `TAVILY_API_KEY` | **Yes** | Used by the Support and Oppose agents to search the live internet for evidence. |
| `PINECONE_API_KEY` | Optional | Used for querying internal vector databases (disabled by default in Free Tier deployments due to memory limits). |
| `PINECONE_INDEX_NAME` | Optional | The name of the Pinecone index if vector search is enabled. |
| `LANGFUSE_SECRET_KEY` | Optional | Used for LLM observability and tracing logs. |
| `LANGFUSE_PUBLIC_KEY` | Optional | Public key for Langfuse tracing. |
| `LANGFUSE_HOST` | Optional | Host URL for Langfuse. |
| `GOOGLE_FACT_CHECK_API_KEY` | Optional | A secondary fallback API for checking existing fact-checks. |

---

## Backend Python Dependencies (`requirements.txt`)

*Note: Heavy machine learning libraries like `torch` and `sentence-transformers` were intentionally removed to allow deployment on 512MB RAM cloud tiers.*

### Core Infrastructure
- `fastapi`: The web framework for handling API routes and SSE streams.
- `uvicorn[standard]`: The ASGI server that runs FastAPI.
- `python-multipart`: Required by FastAPI to process `UploadFile` (images).
- `sse-starlette`: Handles Server-Sent Events (SSE) to stream text to the frontend.
- `pydantic`: Validates JSON schemas.

### AI & Orchestration
- `langgraph`: The state-machine framework orchestrating the Debate.
- `langchain`, `langchain-community`, `langchain-text-splitters`: Helpers for chaining prompts.
- `groq`, `langchain-groq`: SDKs to communicate with the Groq inference engine.
- `instructor`: Extracts structured Pydantic objects out of raw LLM JSON output.

### Web Scraping & Retrieval
- `tavily-python`: Connects to the Tavily search engine.
- `playwright`: A headless browser used to bypass bot-blockers and scrape raw HTML.
- `beautifulsoup4`: Cleans and parses HTML text retrieved by Playwright.
- `pinecone`: SDK for vector database retrieval.

### Database & Rate Limiting
- `sqlalchemy`, `alembic`: Manages the SQLite database (`history.db`) for storing previous fact checks.
- `slowapi`: Implements IP-based rate limiting to protect the server from spam.

---

## Frontend Node Dependencies (`package.json`)

Located inside the `frontend_v2/` directory.

- `next`: The React framework powering the UI.
- `react`, `react-dom`: Core UI libraries.
- `tailwindcss`: Utility-first CSS framework for styling.
- `lucide-react`: SVG icon library.
- `framer-motion`: Handles the smooth animations (e.g., the progress bar and expanding result cards).
