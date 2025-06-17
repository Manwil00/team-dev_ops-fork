# Problem Statement – Niche Explorer

## 1. Problem
Since Researchers, Founders and Product Managers all share the core need to discover, evaluate and act on emerging trends, we decided to consolidate them into a single "Innovator" persona based on their shared goal of identifying trends, understanding why they matter and rapidly turning those insights into research directions or product opportunities.

![image](https://hackmd.io/_uploads/H1nPN87Wxg.png)
*Source: [weagree.com](https://weagree.com/weblog/adopting-innovations-product-lifecycle/)*
## 2. Solution
We propose **Niche Explorer**, a web-based platform designed specifically to uncover and analyze early signals from decentralized online communities. By continuously aggregating content, highlighting rapid growth trends and clustering early-stage research topics, Niche Explorer provides founders, innovators and researchers actionable insights to validate startup ideas, design targeted products and strategically pursue emerging fields of research at their earliest stages.

## 3. User Scenarios
- Researcher: "Highlight preprint keywords in solid‑state batteries with the steepest citation growth in the last 90 days."
- Founder: "Show fast‑growing keywords in longevity discussions and give me a one‑sentence reason each is trending."  

## Initial System Structure
### Core Idea:
1.  **Prompt:** Input your niche query (e.g., "Show fast‑growing trends in CV for 3D registration").
2.  **App Targets Sources:**
    Detects if query is 
    *   "research" (-> arXiv `cs.CV`) [https://rss.arxiv.org/rss/cs.CV]  
    *   "community" (-> Reddit `r/computervision`) [https://www.reddit.com/r/computervision.rss].
    Targets relevant RSS feeds based on this.
3.  **App Skims Latest :** Fetches newest N articles from targeted feeds.
4.  **AI Finds Latest Trends:** Uses embeddings & clustering on this fresh batch to spot 2-3 key themes (e.g., "NeRF").
5.  **Final report:**
    *   **Retrieves:** Relevant text snippets from the fetched articles.
    *   **Generates:** A concise explanation of the theme's significancemarkdown
6. Save in chat log and everytime its openend again only update RSS feed with new entries and redo analysis. (= live digest)

```
User ──► React Front-End (Vite) ──► Spring-Boot API-Server
                                          │
                                          │ REST
                                          ▼
                          ┌────────────────────────────────────┐
                          │   GenAI Service  (FastAPI + Gemini)│
                          │   • POST /classify  (pick feed)    │
                          │   • POST /describe (explain trend) │
                          └────────────────────────────────────┘
                                          │  RSS URL
                                          ▼
                         External Feed (arXiv subject  OR  Reddit subreddit)
```
1. **Query classification** – API-server asks `/classify`; Gemini returns `{source, feed}`.
2. **Fetching** – API pulls the newest *N* items from that RSS feed.
3. **Keyword clustering** – frequency-based today (embeddings coming).
4. **Explanation** – API calls `/describe` with keyword & titles; Gemini answers with a one-sentence summary.
5. **UI render** – React shows trends, article list, relevance bar, and a *source* link pointing to the exact RSS URL used.

### Micro-services snapshot
| Service | Tech | Responsibility |
|---------|------|----------------|
| `client` | React + Vite | end-user UI |
| `api-server` | Spring Boot 3.2 | gateway, RSS fetch, clustering, calls GenAI |
| `genai` | FastAPI + google-genai | Gemini endpoints `/classify`, `/describe` |
| `monitoring` | Spring Boot | custom Prometheus metrics (WIP) |

## 7. Local Development
```bash
# 1. GenAI (Gemini) service
cd genai
# Copy example env file and add your Google API key
cp .env.example .env   # Create .env file from template
# Edit .env and set GOOGLE_API_KEY=your_key_here from https://makersuite.google.com/app/apikey
# Install Python dependencies
pip install -r config/requirements.txt
# Start FastAPI server on port 8000
uvicorn src.app:app --port 8000

# 2. Java API server
cd ../server
./gradlew :api-server:bootRun

# 3. React front-end
cd ../client
npm install
npm run dev
```
Open http://localhost:5173 and run a query.  In every result card the blue "source" link shows which RSS feed powered that analysis.

---
The architecture is modular: swapping in embedding-based clustering, adding database persistence, or deploying to Kubernetes only requires new services—existing contracts stay intact.

## Docker quick-start (all services)

The repository ships with a **single** `docker-compose.yml` that spins up the three micro-services that currently make up Niche Explorer:

| Service        | Image build context | Exposed port | Purpose |
|----------------|--------------------|--------------|---------|
| `client`       | `./client`         | `80`         | React front-end served via Nginx |
| `api-server`   | `./server`         | `8080`       | Spring-Boot backend – RSS fetch, keyword extraction, calls GenAI |
| `genai`        | `./genai`          | `8000`       | FastAPI wrapper around Google Gemini endpoints (`/classify`, `/describe`) |

> Legacy modules (`monitoring`, `report-generator`, `rss-fetcher`) were removed from the codebase and from the compose file – everything now flows through the three services above.

### Prerequisites

1. Docker + Docker Compose v2
2. A Google API key with access to Gemini models.  Create `.env` at repo root:
   ```bash
   echo "GOOGLE_API_KEY=your_actual_key" > .env
   ```

### Run

```bash
# 1. Ensure .env contains your Gemini key (see prerequisites)
cat .env   # should print at least GOOGLE_API_KEY=****

# 2. Build images & start containers (foreground)
docker compose up --build
# or, start in the background
docker compose up -d --build
```

Useful commands:

```bash
# Stop and remove containers
docker compose down

# Re-build only the Java backend after code changes
docker compose build api-server

# Follow logs for a specific service
docker compose logs -f genai
```

> Tip: when running on Apple Silicon or non-x86 hosts, Docker will build multi-arch images automatically. No extra flags required.

Once all containers are **healthy**, open your browser at http://localhost and start exploring niches 🚀.
