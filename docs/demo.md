# CivicPulse Demo Mode Guide

## Overview

Demo mode provides a fully functional CivicPulse instance with synthetic data for evaluation, hackathons, and development without requiring external services.

## Quick Start (Demo Mode)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd civicpulse
```

### 2. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env - ensure DEMO_MODE=true (default)
# DATABASE_URL should point to a PostgreSQL with PostGIS
```

### 3. Start Database (Docker)

```bash
docker run -d \
  --name civicpulse-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=civicpulse \
  -p 5432:5432 \
  postgis/postgis:15-3.3
```

Wait 10 seconds for database to initialize.

### 4. Run Migrations and Seed

```bash
# Install dependencies (using uv recommended)
uv sync
# or: pip install -r requirements.txt

# Run migrations
uv run alembic upgrade head

# Seed demo data
uv run python scripts/seed.py
```

### 5. Start Backend

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000
API docs at http://localhost:8000/docs

### 6. Start Frontend

```bash
cd ../frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs at http://localhost:5173

### 7. (Optional) Start Agents

```bash
cd ../agents
cp .env.example .env
uv sync

# Terminal 1
uv run python classification_agent.py

# Terminal 2
uv run python duplicate_agent.py

# Terminal 3
uv run python priority_agent.py

# Terminal 4
uv run python routing_agent.py

# Terminal 5
uv run python monitoring_agent.py
```

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@civicpulse.local | admin123 |
| Field Worker | worker@civicpulse.local | worker123 |
| Supervisor | supervisor@civicpulse.local | supervisor123 |
| Citizen | citizen@civicpulse.local | citizen123 |

## Demo Data

The seed script creates:

### Departments
- Roads Department
- Sanitation Department
- Electrical Department
- Water Supply Department
- Drainage Department
- Public Works

### Service Zones
- North Zone
- South Zone
- Central Zone

### Sample Reports (8 reports covering all categories)
1. **Pothole on Main Street** - Verified, High priority
2. **Overflowing garbage at Central Park** - Assigned, Medium priority
3. **Broken streetlight on Residential Lane** - In Progress, Medium priority
4. **Water leakage on Commercial Road** - Resolved, Critical priority
5. **Blocked drain on Lake View Road** - Closed, High priority
6. **Cracked footpath near School** - Under Review, Medium priority
7. **Fallen tree on Highway Access** - Assigned, Safety Escalation
8. **Broken bench in Community Park** - Reported, Low priority

### Assignments & Resolutions
- Reports 1, 2, 3, 4 have field worker assignments
- Reports 1, 4 have resolution evidence submitted
- Report 4 resolution approved by supervisor

### Duplicate Candidates
- Nearby reports for each category to demonstrate detection

## Demo Mode Features

### What Works
- ✅ Full report submission with photo upload (mock storage)
- ✅ AI classification (mock provider)
- ✅ Duplicate detection (geospatial + text similarity)
- ✅ Priority scoring (explainable formula)
- ✅ Department routing (configurable rules)
- ✅ Complete status lifecycle
- ✅ Role-based access control
- ✅ Interactive map with clustering
- ✅ Admin dashboard with analytics
- ✅ Field worker task management
- ✅ Supervisor resolution review
- ✅ Notifications (in-app)
- ✅ Dark/Light theme
- ✅ Audit logging

### What's Mocked
- 🎭 AI Vision (uses text-based keyword matching)
- 🎭 File Storage (local mock, no actual upload)
- 🎭 Email/SMS notifications (in-app only)
- 🎭 Fetch.ai Agents (run locally if started)
- 🎭 Real-time updates (polling-based)

### Limitations
- ❌ No real Supabase integration
- ❌ No actual file persistence
- ❌ No external API calls
- ❌ Data resets on database restart
- ❌ No production security hardening

## Demo Scenarios

### Scenario 1: Citizen Submits Report
1. Login as `citizen@civicpulse.local`
2. Click "Submit New Report"
3. Fill form, add photo, pick location on map
4. Submit → Get tracking ID (e.g., CP12345678)
5. View report in "My Reports"
6. Watch status updates

### Scenario 2: Admin Reviews & Assigns
1. Login as `admin@civicpulse.local`
2. Go to Admin Dashboard
3. View reports table with filters
4. Click report → View AI analysis
5. Check duplicates → Confirm/Reject
6. Assign to department/worker
7. Set SLA deadline

### Scenario 3: Field Worker Completes Work
1. Login as `worker@civicpulse.local`
2. View "Field Tasks"
3. Accept assignment
4. Start work → Mark in progress
5. Upload before/after photos
6. Add work notes
7. Submit resolution

### Scenario 4: Supervisor Reviews
1. Login as `supervisor@civicpulse.local`
2. View "Supervisor Queue"
3. Review resolution evidence
4. Approve/Reject/Request rework
5. Report auto-closes on approval

### Scenario 5: Map Exploration
1. Go to "Map View" (any role)
2. See all reports clustered
3. Filter by category, status, priority
4. Click markers for details
5. View hotspots (heatmap)
6. Toggle legend

## Resetting Demo Data

```bash
cd backend
uv run python scripts/seed.py
# Or drop and recreate:
uv run alembic downgrade base
uv run alembic upgrade head
uv run python scripts/seed.py
```

## Switching to Production Mode

1. Set `DEMO_MODE=false` in backend `.env`
2. Configure real Supabase credentials
3. Set `VISION_PROVIDER=openai` (or other) with API key
4. Set real agent seeds and endpoints
5. Configure email provider
6. Run with production ASGI server (gunicorn + uvicorn workers)
7. Deploy frontend to Vercel/Netlify
8. Deploy agents as separate services
9. Set up monitoring and backups

## Troubleshooting

### Database Connection Failed
- Ensure PostgreSQL is running with PostGIS
- Check DATABASE_URL format
- Verify database exists

### Migration Errors
- Run `alembic downgrade base` then `alembic upgrade head`
- Check for conflicting migrations

### Frontend Can't Connect to Backend
- Check VITE_API_BASE_URL in frontend/.env
- Verify CORS_ALLOWED_ORIGINS in backend/.env
- Check Vite proxy config (vite.config.ts)

### Agents Not Responding
- Check agent ports (8001-8005) are free
- Verify agent endpoints in backend config
- Check agent logs for errors

### Map Not Loading
- Check Leaflet CSS import
- Verify map container has height
- Check browser console for errors

## Demo Mode Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        DEMO MODE                              │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Vite)          Backend (FastAPI)                 │
│  - React + TS             - Mock AI Classification           │
│  - Leaflet Map            - Mock Duplicate Detection         │
│  - Theme Toggle           - Mock Priority Scoring            │
│                           - Mock File Storage                │
│                           - In-memory Notifications          │
│                                                             │
│  Agents (Optional)                                           │
│  - Classification Agent (Mock)                               │
│  - Duplicate Agent (Mock)                                    │
│  - Priority Agent (Mock)                                     │
│  - Routing Agent (Mock)                                      │
│  - Monitoring Agent (Mock)                                   │
└─────────────────────────────────────────────────────────────┘
```

## Customizing Demo Data

Edit `backend/scripts/seed.py` to:
- Add/remove sample reports
- Change report locations
- Modify categories and departments
- Adjust priorities and statuses
- Add more users with different roles

## Performance in Demo Mode

- All operations are fast (mock services)
- Map renders 500+ reports smoothly
- No external API latency
- Suitable for live demos and recordings