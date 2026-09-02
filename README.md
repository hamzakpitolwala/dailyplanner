# DailyPlanner - AI-Powered Schedule Management

DailyPlanner is a next-generation, AI-driven scheduling application designed to help you organize your tasks, optimize your daily routine, and reflect on your productivity patterns. Through an integrated **Multi-Agent AI System**, the app actively monitors your schedules, suggests personalized improvements, and provides conversational assistance. 

Recently enhanced with **Model Context Protocol (MCP)**, DailyPlanner seamlessly integrates its advanced AI workflows to interact with various tools, contexts, and user memory efficiently.

---

## 🚀 Key Features

* **Multi-Agent AI Engine:** A state-machine-driven orchestrator managing specialized agents (Planner, Chat, Insight, Recommendation, Verification).
* **Intelligent Scheduling & Timeline:** A dynamic, visual timeline (TimelineAxis) that organizes your tasks, highlights focus blocks, and alerts on schedule overlaps.
* **Model Context Protocol (MCP) Integration:** Exposes planner tools, analytics, and memory contexts via an MCP server (`fastmcp`), extending the AI's capabilities natively.
* **Contextual Memory & Insights:** The AI engine remembers past disruptions, reasons for missed tasks, and adapts to your *Productivity Velocity* and *Personality Type* over time.
* **Calendar Syncing:** Seamless integration with Google Calendar and other external scheduling tools.
* **Templates & Checklists:** Build recurring routines using templates with predefined subtasks.
* **Secure Authentication:** OAuth integration (Google & GitHub) alongside robust JWT-based local authentication.
* **Production-Ready:** Fully containerized with Docker, covered by an automated test suite (`pytest`), and integrated with a GitHub Actions CI/CD pipeline.

---

## 🏗️ Tech Stack & Architecture

### Backend
* **Framework:** FastAPI (Python 3.12)
* **Database:** PostgreSQL (with SQLAlchemy 2.0 Async driver + asyncpg)
* **AI & Orchestration:** Ollama (qwen2.5:7b), LangGraph/LangChain, FastMCP
* **Testing:** Pytest with in-memory SQLite support (`aiosqlite`) via `.venv`

### Frontend
* **Framework:** React 18, TypeScript, Vite
* **Styling:** Tailwind CSS (Modern, Responsive UI)
* **API Integration:** Axios

### Infrastructure
* **Containerization:** Docker & Docker Compose (`docker-compose.yml`, `docker-compose.prod.yml`)
* **Web Server:** Nginx (for serving the React frontend in production)
* **CI/CD:** GitHub Actions (`.github/workflows/ci-cd.yml`) pushing to GitHub Container Registry (GHCR).

---

## 💻 Getting Started (Local Development)

### Prerequisites
* Docker and Docker Compose
* Python 3.12+ (for running tests/backend locally)
* Node.js 20+ (for frontend development)
* Ollama (installed locally and running `qwen2.5:7b` for AI features)

### 1. Environment Setup

Clone the repository and set up your environment variables. 
```bash
git clone git@github.com:hamzakpitolwala/dailyplanner.git
cd dailyplanner

# Copy the example environments
cp .env.example .env
```
Ensure that your `.env` contains the correct database credentials and OAuth keys if you plan to use third-party sign-in.

### 2. Running with Docker (Recommended)

To spin up the entire application (PostgreSQL, Backend, Frontend) with hot-reloading:

```bash
docker compose up --build
```
* **Frontend UI:** `http://localhost:8080` (or `http://localhost:5173` if running outside docker)
* **Backend API Docs (Swagger):** `http://localhost:8000/docs`

### 3. Running Manually (Without Docker)

**Backend Setup:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI server
uvicorn backend.main:app --reload
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

---

## 📖 Workflow & How to Use

1. **Onboarding:** Create an account (or sign in via Google/GitHub). Set up your basic profile, structure preferences, and typical focus times.
2. **Planning the Day:** Add tasks with specific times or allocate them to categories. The timeline will visually stack your tasks.
3. **Interacting with AI (Planner AI):** 
   - Click the chat interface to talk to the AI.
   - Example prompts: *"Can you suggest a better time for my deep work session today?"* or *"Analyze my schedule from yesterday."*
   - The Orchestrator will route your request to the appropriate agent (Chat, Insight, or Planner) using the MCP tools.
4. **Memory Concept:** As you complete or miss tasks, the AI stores these insights in its Memory Manager, updating your `Productivity Velocity` and using past contexts to tailor future recommendations.
5. **Checking In:** Mark tasks as completed, partial, or skipped. Provide reasons (e.g., "Got distracted") so the AI learns your typical disruptions.

---

## 🧪 Testing

The backend contains a robust automated test suite. 

To run the tests locally:
```bash
source .venv/bin/activate
# Install requirements if you haven't already
pip install -r requirements.txt

# Run the test suite
PYTHONPATH=. pytest tests/
```
*Note: The test suite runs automatically on a fast in-memory SQLite database (`aiosqlite`), configured via `tests/conftest.py`.*

---

## 🚢 Deployment

The project is configured for automated CI/CD via GitHub Actions.

1. Any push to `main` triggers `.github/workflows/ci-cd.yml`.
2. The pipeline checks out the code, runs the test suite, and upon success, builds the production Docker images.
3. The images are tagged and pushed to the GitHub Container Registry (`ghcr.io`).

**To deploy in production using the built images:**
```bash
# Set your environment variables (like DATABASE_URL, BACKEND_IMAGE, etc.)
docker compose -f docker-compose.prod.yml up -d
```
