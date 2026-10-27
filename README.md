# CivicPulse

"Every Report Matters. Every Issue Has a Path to Resolution."

An AI-powered civic issue intelligence and resolution platform combining computer vision, geospatial analytics, community participation, and Fetch.ai autonomous agents.

## Architecture

```
civicpulse/
├── frontend/          # React + Vite + TypeScript + Tailwind CSS
├── backend/           # FastAPI + PostgreSQL + PostGIS
├── agents/            # Fetch.ai uAgents (Classification, Duplicate, Priority, Routing, Monitoring)
├── database/          # Migrations, seeds, RLS policies
├── docs/              # Architecture, API, deployment docs
└── scripts/           # Utility scripts
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ with PostGIS (or Supabase)
- uv (recommended) or pip

### Development Setup

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your configuration
uv sync  # or pip install -r requirements.txt
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload

# Frontend
cd frontend
cp .env.example .env
npm install
npm run dev

# Agents (in separate terminals)
cd agents
cp .env.example .env
uv sync
uv run python classification_agent.py
uv run python duplicate_agent.py
uv run python priority_agent.py
uv run python routing_agent.py
uv run python monitoring_agent.py
```

### Demo Mode
Set `DEMO_MODE=true` in backend/.env to use synthetic data and mock AI providers. See `docs/demo.md` for detailed demo instructions.

## Key Features

- **Citizen Reporting**: Photo upload, GPS/map location, category selection, duplicate warnings
- **AI Classification**: Image + text analysis with confidence scores and explanations
- **Duplicate Detection**: Geospatial + semantic similarity with review workflow
- **Priority Scoring**: Explainable formula (severity, risk, time, corroboration)
- **Department Routing**: Configurable category-to-department mapping
- **Fetch.ai Agents**: Autonomous classification, duplicate, priority, routing agents
- **Full Lifecycle**: Reported → Review → Verified → Assigned → In Progress → Resolved → Closed
- **Role-Based Access**: Citizen, Admin, Field Worker, Supervisor, Public Viewer
- **Map Visualization**: Leaflet + OpenStreetMap with clustering, heatmaps, filters
- **Analytics Dashboard**: Hotspots, trends, department workload, SLA metrics
- **Dark/Light Theme**: System-aware theme with manual toggle
- **Responsive Design**: Mobile-first, accessible UI

## Environment Variables

See `.env.example` in each component directory.

## Testing

```bash
# Backend tests
cd backend && uv run pytest

# Frontend tests
cd frontend && npm test

# Agent tests
cd agents && uv run pytest
```

## Documentation

- [Deployment Guide](docs/deployment.md)
- [Demo Mode Guide](docs/demo.md)
- [API Documentation](docs/api.md) (when available)
- [Agent Architecture](docs/agents.md) (when available)

## License

MIT