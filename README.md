# 🏠 UIUC Housing Assistant

An AI-powered housing search tool for UIUC students. Ask in plain English — get real, ranked listings from Champaign landlords.

> *"2 bedroom under $900/bed near campus"* → instant results from Green Street Realty, with prices, availability, and direct links.

---

## What It Does

Most UIUC students search for housing on Apartments.com or Craigslist, where listings are often stale, mis-priced, or already rented. This tool goes directly to the source — scraping major Champaign landlords — and lets students search using natural language instead of filters.

Built as an original portfolio project to demonstrate production-ready AI engineering skills: RAG pipeline design, local LLM integration, web scraping, and full-stack deployment.

---

## Demo

![App screenshot placeholder](docs/screenshot.png)

*Streamlit chat UI — ask a question, get a comparison table with address, unit type, price range, availability, and a direct link.*

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Ollama · `llama3.1:8b` (local, no API cost) |
| **RAG framework** | LangChain + Chroma vector store |
| **Embeddings** | `all-MiniLM-L6-v2` via `sentence-transformers` |
| **Scraping** | Playwright (headless Chromium) |
| **Database** | SQLite |
| **Frontend** | Streamlit |
| **Language** | Python 3.14 |

---

## Project Structure

```
ai/
├── scrapers/
│   └── green_street.py         # Playwright scraper → green_street_raw.json
├── normalize_green_street.py   # Cleans raw JSON → SQLite
├── ingest.py                   # Embeds listings into Chroma vector store
├── rag_chain.py                # Retriever + LLM chain
├── app.py                      # Streamlit chat UI
├── green_street_raw.json       # Raw scraped data (489 floor plans)
├── green_street_listings.db    # Normalized SQLite database
├── chroma_db/                  # Persisted vector store
└── design_docs/                # Research notes and phase docs
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd uiuc-housing-assistant-langchain-rag
python3 -m venv .venv 
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install langchain langchain-ollama langchain-community langchain-core \
            chromadb sentence-transformers streamlit \
            playwright pandas sqlite-utils python-dotenv
playwright install chromium
```

### 3. Install and start Ollama

```bash
brew install ollama
brew services start ollama
ollama pull llama3.1:8b
```

---

## Running the Pipeline

Run these once to build the data layer, then launch the app.

```bash
# Step 1 — Scrape Green Street Realty
python scrapers/green_street.py
# → green_street_raw.json  (489 floor plans · 251 properties)

# Step 2 — Normalize and store in SQLite
python normalize_green_street.py
# → green_street_listings.db

# Step 3 — Embed listings into Chroma
python ingest.py
# → chroma_db/  (first run downloads ~90 MB embedding model)

# Step 4 — Launch the app
streamlit run app.py
# → http://localhost:8501
```

---

## Data Sources

| Company | Status | Method |
|---|---|---|
| **Green Street Realty** | ✅ Live | Playwright scraper |
| Universities Group | 🔜 Planned | Playwright scraper |
| MHM Properties | 🔜 Planned | Playwright scraper |
| Here 707 | 🔜 Planned | TBD |
| Hub on Campus | 🔜 Planned | TBD |

All scrapers respect each site's `robots.txt` and `Crawl-delay` directive.


---

## Roadmap

- [ ] Add Universities Group scraper
- [ ] Add MHM Properties scraper
- [ ] Weekly auto-refresh scheduler (`refresh.py`)
- [ ] Deploy to Railway with OpenAI API swap
- [ ] Distance-to-campus filter
- [ ] Saved searches / favorites

---

## Acknowledgements

Learning path inspired by [瓦子's guide on Xiaohongshu](https://www.xiaohongshu.com/explore/69c9a6400000000023021345) on breaking into AI engineering roles. RAG architecture based on AI Jason's LangGraph tutorials.
