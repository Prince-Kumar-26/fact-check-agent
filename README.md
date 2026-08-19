# AI Multi-Agent Fact Check Debate Engine ⚖️ (V2)

A production-grade, multi-agent AI system designed to rigorously fact-check claims using a simulated debate. The system takes a claim, independently retrieves evidence to both support and oppose it, and then sets two autonomous LLM agents to cross-examine each other in real-time. Finally, an impartial AI judge issues a definitive verdict.

## 🌟 Key Features (V2 Upgrades)

*   **Multi-Turn LangGraph Debate**: A `Support Agent` and an `Oppose Agent` engage in a multi-round debate. They cross-examine each other's cases to test the structural integrity of the arguments.
*   **Real-Time SSE Streaming**: Watch the debate unfold live! LangGraph agents instantly stream their arguments to the frontend word-by-word.
*   **Security & Rate Limiting**: Built-in IP-based rate limiting via `slowapi` and strict prompt injection sanitization to protect LLM quotas.
*   **Next.js Neumorphic Frontend**: Upgraded to a robust Next.js React frontend, featuring beautiful neumorphic components, micro-animations, and a highly responsive design.
*   **Multi-Modal Fact Checking**: Users can upload images (e.g. screenshots of tweets or news articles). The backend uses **Gemini 1.5 Pro Vision** to extract claims directly from the image before routing to the debate graph.
*   **Asymmetric Dual Retrieval**: The system actively searches for evidence that *proves* the claim, and separately searches for evidence that *disproves* it.
*   **Deep Web Scraping**: Integrates **Tavily** for live web search and **Playwright** for deep DOM scraping to ensure complete context is extracted from URLs.
*   **SQLite Caching**: All fact-check debates are persistently cached in a local SQLite database (`history.db`) so repeated queries resolve instantly without consuming LLM tokens.
*   **Strict Citation Enforcement**: Debater agents are strictly prompted to use `[1]`, `[2]` inline citations that map directly to their retrieved documents, mitigating hallucinations.

## 🏗️ Architecture

The backend is built with **FastAPI** and the frontend is built with **Next.js**. 
For an in-depth view of the system diagrams and data flow, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## 🚀 Getting Started

### Prerequisites
- Node.js & npm (for frontend)
- Python 3.10+ (for backend)
- Playwright browsers installed
- API Keys for: Groq, Gemini, and Tavily.

### 1. Backend Setup
Clone the repository and set up a virtual environment:
```bash
python -m venv .venv
# Activate on Windows:
.\.venv\Scripts\activate
# Activate on Mac/Linux:
source .venv/bin/activate
```

Install all dependencies and browser binaries:
```bash
pip install -r backend/requirements.txt
playwright install chromium
```

### 2. Configuration
Create a `.env` file in the root directory. Ensure the following variables are set:
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`

### 3. Running the System

Start the FastAPI backend server:
```bash
# From the root directory:
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Start the Next.js frontend server:
```bash
cd frontend_v2
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

## 📁 Repository Structure
```text
fact_check_agent/
├── backend/
│   ├── api.py               # FastAPI server and SSE streaming logic
│   ├── agents.py            # Debaters, Judge logic, and ChatGroq configs
│   ├── graph.py             # LangGraph state machine configuration
│   ├── layer_extractor.py   # Guardrails, claim extraction, and Gemini Vision
│   ├── retrieval_router.py  # Tavily retrieval and Playwright scraping
│   ├── schemas.py           # Pydantic models for structured output
│   ├── database.py          # SQLite configuration
│   └── models.py            # SQLAlchemy database models
├── frontend_v2/
│   ├── src/app/             # Next.js App Router (page.tsx, layout.tsx, etc.)
│   ├── src/components/      # Reusable React components
│   ├── package.json         # Node dependencies
│   └── tailwind.config.ts   # Tailwind CSS configuration
├── history.db               # SQLite persistent cache (auto-generated)
├── requirements.txt         # Global Python dependencies
└── .env                     # Secrets configuration
```

## ⚠️ Disclaimer
This system uses experimental LLMs and autonomous agents. While the strict inline citations and dual-retrieval significantly lower hallucination rates, the AI Judge can still make mistakes. Always verify critical health or scientific information independently.
