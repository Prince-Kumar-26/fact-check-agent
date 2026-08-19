# 🔍 Fact-Check Agent V2

[![Frontend Deploy](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel)](https://fact-check-agent-theta.vercel.app)
[![Backend Deploy](https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render)](https://fact-check-agent-backend-rkqi.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)

An autonomous, multi-agent AI system designed to rigorously fact-check claims using a simulated courtroom debate. It leverages LangGraph to orchestrate a Support Agent, an Oppose Agent, and a Judge Agent who cross-examine evidence scraped dynamically from the web to reach a final, highly-confident verdict.

---

## 🌐 Live Demo
- **Frontend (Vercel)**: [https://fact-check-agent-theta.vercel.app](https://fact-check-agent-theta.vercel.app)
- **Backend API (Render)**: [https://fact-check-agent-backend-rkqi.onrender.com/docs](https://fact-check-agent-backend-rkqi.onrender.com/docs)

---

## ✨ Key Features
- **Multi-Agent Debate Framework**: A LangGraph state machine where AI agents actively debate each other to eliminate bias.
- **Dynamic Web Scraping**: Integrates Tavily API and Playwright to deeply scrape web sources and extract verifiable evidence.
- **Multimodal Support**: Upload images containing text (e.g., social media screenshots), and the system extracts the claims using Vision models before fact-checking them.
- **Real-Time Streaming**: Server-Sent Events (SSE) stream the debate live to a sleek Next.js UI, keeping the user engaged while the heavy reasoning happens in the background.
- **Full Cloud Deployment**: Dockerized backend optimized for Render (handling Chromium dependencies), and a serverless frontend hosted on Vercel.

---

## 🏗️ Architecture Overview
The backend is built with **FastAPI** and **LangGraph**, relying on **Groq** (`gpt-oss-120b`) for lightning-fast LLM inference. 
The system operates in phases:
1. **Extraction**: Parse user text or extract claims from an uploaded image.
2. **Debate Phase**: Support and Oppose agents independently search the web, scrape articles, and construct their initial cases.
3. **Cross-Examination**: Agents review each other's cases and formulate rebuttals.
4. **Judgment**: A Judge agent parses the entire transcript and returns a structured JSON verdict with a confidence score and citations.

*For a deep dive into the system design, see [ARCHITECTURE.md](./documentations/ARCHITECTURE.md).*

---

## 🚀 Quick Start (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/Prince-Kumar-26/fact-check-agent.git
cd fact-check-agent
```

### 2. Backend Setup
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Setup Environment Variables
cp .env.example .env
# Edit .env with your GROQ_API_KEY, TAVILY_API_KEY, etc.

# Start the FastAPI server
uvicorn backend.api:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend_v2

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 📚 Documentation
Comprehensive documentation is available in the `documentations/` folder:
- **[PROJECT_MANUAL.md](./documentations/PROJECT_MANUAL.md)**: The ultimate "Start to Finish" guide on how this project was built and how it works.
- **[ARCHITECTURE.md](./documentations/ARCHITECTURE.md)**: Detailed system design, AI node flows, and database schemas.
- **[TIMELINE.md](./documentations/TIMELINE.md)**: A chronological history of the development phases and hurdles overcome.
- **[DEPENDENCIES.md](./documentations/DEPENDENCIES.md)**: Complete breakdown of required API keys, Python libraries, and Node packages.

---

## 🛡️ License
This project is licensed under the MIT License.
