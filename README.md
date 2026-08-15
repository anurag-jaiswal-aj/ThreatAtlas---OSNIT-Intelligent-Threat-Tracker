# OSINT Threat Intelligence Platform (TIP)

A defensive intelligence monitoring platform designed to collect publicly available information, process unstructured reports via NLP, extract threat/credibility scores, and visualize events on an interactive 3D globe.

## Current Development Status

> **Current Phase**: Phase 1 — Step 1: Infrastructure Initialization  
> **Note**: Most project functionality (OSINT ingestion, NLP pipelines, threat scoring, frontend globe visualization) has **not** been implemented yet. Currently, only basic project structure, Docker container definitions (MongoDB + Redis), and the FastAPI application foundation with health checks are established.

---

## Prerequisites

- **Docker** and **Docker Compose** (for MongoDB and Redis)
- **Python 3.10+** (for running the backend locally)
- **pip** and **virtualenv**

---

## Getting Started

### 1. Environment Configuration

Copy the sample environment file to `.env`:

```bash
cp .env.example .env
```

### 2. Infrastructure Setup (MongoDB & Redis)

Start the database and caching services using Docker Compose:

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

To verify the containers are running:

```bash
docker compose -f infrastructure/docker-compose.yml ps
```

### 3. Backend Setup

Navigate to the `backend` directory and set up a virtual environment:

```bash
cd backend
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Linux/macOS:
source venv/bin/activate

# Install Phase 1 dependencies:
pip install -r requirements.txt
```

### 4. Running the Backend Server

Start the FastAPI development server:

```bash
python main.py
```

Alternatively, run with Uvicorn directly:

```bash
uvicorn main:app --reload --port 8000
```

---

## Health Check Verification

Once the backend server is running, verify system status:

- **Root Health Check**:  
  `GET http://localhost:8000/health`
  
- **API v1 Health Check**:  
  `GET http://localhost:8000/api/v1/health`

### Expected Response

```json
{
  "status": "ok",
  "project": "OSINT Threat Intelligence Platform",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## Project Structure

```text
ThreatAtlas/
├── backend/
│   ├── app/
│   │   ├── api/            # API routers & endpoints
│   │   ├── core/           # Config (pydantic-settings) & logging
│   │   ├── db/             # Database connection & models
│   │   ├── ingestion/      # OSINT data collectors
│   │   ├── nlp/            # spaCy, EntityRuler & Embeddings
│   │   ├── intelligence/   # Clustering & Scoring algorithms
│   │   ├── services/       # Business logic layer
│   │   └── websockets/     # Real-time WebSocket handlers
│   ├── tests/              # Test suite
│   ├── main.py             # FastAPI entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # Frontend React application (Phase 4)
├── infrastructure/         # Docker Compose & container setups
│   └── docker-compose.yml  # MongoDB & Redis definitions
├── .env.example            # Baseline environment variables
├── .gitignore
└── README.md
```
