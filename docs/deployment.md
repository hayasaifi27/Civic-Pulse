# CivicPulse Deployment Guide

## Overview

This guide covers deploying CivicPulse to production environments.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Database   │
│  (Vercel)   │     │  (Railway/  │     │  (Supabase) │
│             │     │   Render)   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Agents    │
                    │  (Separate  │
                    │  Services)  │
                    └─────────────┘
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ with PostGIS
- Supabase account (recommended) or self-hosted PostgreSQL
- Domain name with SSL

## Environment Variables

### Backend (.env)

```bash
APP_ENV=production
API_BASE_URL=https://api.yourdomain.com
DEBUG=false

DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/civicpulse
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=civicpulse-media

VISION_PROVIDER=mock  # or openai/anthropic/google
VISION_API_KEY=your-vision-api-key
VISION_MODEL=gpt-4-vision-preview

AGENT_MODE=production
AGENT_SEED=your-secure-random-seed-32-chars-min
AGENT_ENDPOINT=https://api.yourdomain.com/agent/webhook

CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

EMAIL_PROVIDER=sendgrid  # or resend/mailgun
EMAIL_API_KEY=your-email-api-key
EMAIL_FROM=noreply@yourdomain.com

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

DEMO_MODE=false

MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=image/jpeg,image/png,image/webp,image/heic

SECRET_KEY=your-very-secure-secret-key-32-chars-minimum
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
REFRESH_TOKEN_EXPIRY_DAYS=30
```

### Frontend (.env)

```bash
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_DEFAULT_THEME=system
```

### Agents (.env)

```bash
CLASSIFICATION_AGENT_SEED=your-classification-seed
DUPLICATE_AGENT_SEED=your-duplicate-seed
PRIORITY_AGENT_SEED=your-priority-seed
ROUTING_AGENT_SEED=your-routing-seed
MONITORING_AGENT_SEED=your-monitoring-seed

CLASSIFICATION_AGENT_PORT=8001
DUPLICATE_AGENT_PORT=8002
PRIORITY_AGENT_PORT=8003
ROUTING_AGENT_PORT=8004
MONITORING_AGENT_PORT=8005

CLASSIFICATION_AGENT_ENDPOINT=https://agents.yourdomain.com/classification/submit
DUPLICATE_AGENT_ENDPOINT=https://agents.yourdomain.com/duplicate/submit
PRIORITY_AGENT_ENDPOINT=https://agents.yourdomain.com/priority/submit
ROUTING_AGENT_ENDPOINT=https://agents.yourdomain.com/routing/submit
MONITORING_AGENT_ENDPOINT=https://agents.yourdomain.com/monitoring/submit

FUND_AGENT=false
```

## Database Setup

### Supabase (Recommended)

1. Create a new Supabase project
2. Enable PostGIS extension: `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Run migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
4. Seed initial data:
   ```bash
   python scripts/seed.py
   ```

### Self-hosted PostgreSQL

1. Install PostgreSQL 15+ with PostGIS
2. Create database and user
3. Run migrations and seed as above

## Backend Deployment

### Railway (Recommended)

1. Connect GitHub repo to Railway
2. Set environment variables
3. Add PostgreSQL service
4. Configure build:
   ```dockerfile
   # Railway auto-detects Python
   # Just set start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Render

1. Create Web Service
2. Build command: `pip install -r requirements.txt && alembic upgrade head`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

### Docker

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN alembic upgrade head

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Frontend Deployment

### Vercel (Recommended)

1. Connect GitHub repo
2. Set framework: Vite
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variables
6. Configure rewrites for SPA:
   ```json
   {
     "rewrites": [
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```

### Netlify

Similar to Vercel, configure build command and environment variables.

### Docker

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Agents Deployment

Agents run as separate services. Options:

### Option 1: Separate Containers (Recommended)

Each agent in its own container:
```dockerfile
# agents/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "classification_agent.py"]
```

Deploy 5 containers (classification, duplicate, priority, routing, monitoring).

### Option 2: Single Process with Multiple Agents

Run all agents in one process (development only).

### Option 3: Serverless Functions

Deploy each agent as a separate serverless function (AWS Lambda, Cloud Run).

## Agent-Backend Communication

The backend communicates with agents via HTTP webhooks:

1. Backend sends request to agent endpoint
2. Agent processes and sends response back to backend webhook
3. Backend stores results

Configure webhook URLs in agent `.env` files.

## SSL/TLS

- Use Let's Encrypt or Cloudflare for automatic SSL
- Ensure all API endpoints use HTTPS
- Configure CORS for production domains only

## Monitoring

### Health Checks

- `GET /health` - Basic health
- `GET /health/db` - Database connectivity
- `GET /health/agents` - Agent status
- `GET /health/ready` - Readiness probe

### Logging

- Structured JSON logs via structlog
- Ship to: Datadog, Logtail, or self-hosted ELK

### Metrics

- Prometheus metrics at `/metrics`
- Key metrics: request latency, error rate, agent response time

## Backup Strategy

### Database

- Supabase: Automatic daily backups
- Self-hosted: `pg_dump` daily, retain 30 days
- Test restore monthly

### File Storage

- Supabase Storage: Versioned, replicated
- Self-hosted: Sync to S3/GCS

## Scaling Considerations

### Backend

- Horizontal scaling with load balancer
- Connection pooling (PgBouncer)
- Redis for caching/sessions

### Agents

- Each agent type can scale independently
- Use message queue (Redis/RabbitMQ) for high throughput
- Monitor agent queue depth

### Database

- Read replicas for analytics queries
- Partition large tables by date
- Index optimization

## Security Checklist

- [ ] All secrets in environment variables (never in code)
- [ ] HTTPS everywhere
- [ ] CORS restricted to production domains
- [ ] Rate limiting enabled
- [ ] JWT secrets rotated periodically
- [ ] Database credentials rotated
- [ ] Agent seeds are unique and secure
- [ ] File upload validation and sanitization
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (CSP headers)
- [ ] Regular dependency updates

## CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      - name: Frontend tests
        run: |
          cd frontend
          npm ci
          npm test
      - name: Agent tests
        run: |
          cd agents
          pip install -r requirements.txt
          pytest

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        # Railway CLI deploy

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        # Vercel CLI deploy
```

## Rollback Procedure

1. Database: Restore from latest backup
2. Backend: Deploy previous Docker image/tag
3. Frontend: Vercel/Netlify instant rollback
4. Agents: Restart with previous version

## Support Contacts

- Backend issues: Check `/health` endpoints
- Agent issues: Check agent logs
- Database: Supabase dashboard or pgAdmin
- Frontend: Browser dev tools + Vercel logs