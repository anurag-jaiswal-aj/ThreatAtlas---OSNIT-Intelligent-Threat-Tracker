# ThreatAtlas — OSINT Threat Intelligence Platform

A defensive intelligence monitoring platform designed to collect publicly available information, process unstructured reports via NLP, extract threat/credibility scores, and visualize events on an interactive 3D CesiumJS globe.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.10+), spaCy NER, Geocoding, MongoDB, Redis Pub/Sub, WebSockets
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, CesiumJS 3D Globe
- **Database & Cache**: MongoDB (Geospatial 2dsphere indexing) & Redis

---

## Quick Start Guide

### 1. Start Infrastructure (MongoDB & Redis)

Make sure Docker is running, then launch the database and cache containers:

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

---

### 2. Start the Backend API Server

Open a terminal window and run:

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

> **Backend Status**: Available at `http://localhost:8000`  
> **Interactive API Docs**: `http://localhost:8000/docs`

---

### 3. Start the Frontend Dashboard

Open a second terminal window and run:

```bash
cd frontend
npm run dev
```

> **Frontend Dashboard**: Open `http://localhost:3000` in your web browser.

---

## Workflow & Features

1. **Ingest OSINT Feeds**: Trigger RSS ingestion via the API or backend CLI script.
2. **Process Intelligence**: Click **"Process Pending OSINT"** in the top navigation bar of the web dashboard to process raw posts through text cleaning, spaCy NER, geocoding, threat scoring, and event clustering.
3. **Explore the 3D Globe**: Filter events by threat level (`High`, `Medium`, `Low`), search keywords, and click markers on the 3D Cesium globe to open transparent score breakdowns and source lists.

---

## Running Test Suites

To verify all 52 unit and integration tests across the backend:

```bash
cd backend
pytest
```

To verify the frontend production build:

```bash
cd frontend
npm run build
```
