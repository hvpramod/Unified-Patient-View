# Local Development Setup Guide (No Docker)

Run the complete Unified Patient View stack natively on your Windows dev machine — no Docker required.

---

## Prerequisites

| Requirement | Version | Download |
|---|---|---|
| Python | 3.12+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| PostgreSQL | 14+ | https://www.postgresql.org/download/windows/ |
| Redis | any | `winget install --id Redis.Redis --source winget` |
| Git | any | https://git-scm.com/ |

> **Note:** PostgreSQL and Redis must be running as services/processes before starting the app.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/hvpramod/Unified-Patient-View.git
cd Unified-Patient-View
git checkout feature/local-run-setup
```

---

## Step 2 — Set Up PostgreSQL

### 2a. Create the database and user

Open **pgAdmin** or **psql** and run:

```sql
CREATE USER upv WITH PASSWORD 'upv' CREATEDB;
CREATE DATABASE upv OWNER upv;
GRANT ALL PRIVILEGES ON DATABASE upv TO upv;
```

### 2b. Install the `uuid-ossp` extension

```sql
\c upv
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 2c. Verify connection

```bash
psql -U upv -d upv -c "SELECT current_user, current_database();"
```

Expected output:
```
 current_user | current_database
--------------+-----------------
 upv          | upv
```

> **Troubleshooting:** If you get `password authentication failed`, check your `pg_hba.conf` file and ensure it allows password auth for `localhost`. The file is usually at `C:\Program Files\PostgreSQL\<version>\data\pg_hba.conf`.

---

## Step 3 — Start Redis

```powershell
# If installed via winget
Start-Process "C:\Program Files\Redis\redis-server.exe" -WindowStyle Hidden

# Verify it's running
& "C:\Program Files\Redis\redis-cli.exe" ping
# Should print: PONG
```

---

## Step 4 — Create Python Virtual Environment

Run from the **repo root**:

```powershell
# Create venv
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1        # PowerShell
# OR
.\.venv\Scripts\activate.bat        # CMD
```

### 4a. Install shared models

```powershell
pip install -e .\packages\shared-models
```

### 4b. Install all backend dependencies

```powershell
pip install `
  fastapi uvicorn[standard] `
  sqlalchemy[asyncio] asyncpg psycopg2-binary alembic `
  httpx redis[hiredis] aiokafka `
  pydantic-settings python-jose[cryptography] `
  structlog tenacity python-dateutil `
  langchain langchain-openai langchain-anthropic langgraph `
  openai anthropic
```

> **Corporate network / SSL issues?** Add `--trusted-host pypi.org --trusted-host files.pythonhosted.org` to all `pip install` commands.

---

## Step 5 — Run Database Migrations

```powershell
cd migrations
$env:DATABASE_URL = "postgresql://upv:upv@localhost:5432/upv"
alembic upgrade head
cd ..
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial UPV schema
```

> **Note:** The `vector` (pgvector) extension is skipped in migrations for local dev. It is only needed for the RAG / clinical guidelines feature. The rest of the app works without it.

---

## Step 6 — Install Frontend Dependencies

```powershell
cd apps\frontend
npm install --legacy-peer-deps
cd ..\..
```

> **Corporate network / SSL issues?** Run `npm config set strict-ssl false` first.

---

## Step 7 — Configure Environment

Copy the dev environment file:

```powershell
Copy-Item .env.dev .env.local
```

Open `.env.local` and fill in your API keys (optional for demo mode):

```env
# Required only if you want real AI-generated summaries
OPENAI_API_KEY=sk-your-real-key-here
ANTHROPIC_API_KEY=sk-ant-your-real-key-here

# Required only for Athena live data
ATHENA_CLIENT_ID=
ATHENA_CLIENT_SECRET=
ATHENA_PRACTICE_ID=

# Leave empty for local dev — Azure AD auth is bypassed
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
```

> **Demo mode:** With placeholder API keys, the AI agent service starts but AI-generated summaries will fail. The demo page (`/demo`) uses hardcoded synthetic data and works with **no API keys at all**.

---

## Step 8 — Start All Services

### Option A — One-click batch file (Recommended)

Double-click **`start-all.bat`** in the repo root.

This opens a minimized terminal window for each service and starts them in the correct order. Wait ~15 seconds for all windows to initialize.

### Option B — PowerShell script

```powershell
.\run-local.ps1
```

### Option C — Start services manually

Run each command in a separate terminal:

```powershell
# Terminal 1 — Mock HealthGorilla (port 8081)
cd mocks\healthgorilla
uvicorn main:app --port 8081

# Terminal 2 — Mock Pathway (port 8082)
cd mocks\pathway
uvicorn main:app --port 8082

# Terminal 3 — Gateway API (port 8000)  ← most important
cd apps\gateway-api
$env:DATABASE_URL="postgresql+asyncpg://upv:upv@localhost:5432/upv"
$env:REDIS_URL="redis://localhost:6379"
uvicorn app.main:app --port 8000 --reload

# Terminal 4 — Ingestion Service (port 8001)
cd apps\ingestion-service
$env:DATABASE_URL="postgresql+asyncpg://upv:upv@localhost:5432/upv"
$env:HEALTHGORILLA_BASE_URL="http://localhost:8081"
$env:PATHWAY_BASE_URL="http://localhost:8082"
uvicorn app.main:app --port 8001

# Terminal 5 — Conflict Detection (port 8003)
cd apps\conflict-detection
$env:DATABASE_URL="postgresql+asyncpg://upv:upv@localhost:5432/upv"
uvicorn app.main:app --port 8003

# Terminal 6 — AI Agent Service (port 8004)
cd apps\ai-agent-service
$env:DATABASE_URL="postgresql+asyncpg://upv:upv@localhost:5432/upv"
$env:REDIS_URL="redis://localhost:6379"
uvicorn app.main:app --port 8004

# Terminal 7 — Notification Service (port 8006)
cd apps\notification-service
uvicorn app.main:app --port 8006

# Terminal 8 — Frontend (port 3000)
cd apps\frontend
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

---

## Step 9 — Verify Everything is Running

Open a new terminal and run:

```powershell
foreach ($port in @(8000, 8001, 8003, 8004, 8006, 8081, 8082, 3000)) {
    try {
        $r = Invoke-WebRequest "http://localhost:$port/" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        Write-Host ":$port  UP" -ForegroundColor Green
    } catch {
        Write-Host ":$port  not ready" -ForegroundColor Red
    }
}
```

Expected output:
```
:8000  UP   ← Gateway API
:8001  UP   ← Ingestion Service
:8003  UP   ← Conflict Detection
:8004  UP   ← AI Agent Service
:8006  UP   ← Notification Service
:8081  UP   ← Mock HealthGorilla
:8082  UP   ← Mock Pathway
:3000  UP   ← Frontend
```

---

## Step 10 — Open the Application

| URL | Description |
|---|---|
| **http://localhost:3000/demo** | Full UI with synthetic patient data — no login required |
| **http://localhost:3000** | Main app (requires Azure AD login in production) |
| **http://localhost:8000/api/docs** | Swagger API documentation |
| **http://localhost:8000/health** | Backend health check |

---

## Stopping All Services

### Option A — Batch file

Double-click **`stop-all.bat`** in the repo root.

### Option B — Manual

Close each terminal window, or run:

```powershell
foreach ($port in @(8000, 8001, 8003, 8004, 8006, 8081, 8082)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}
```

---

## Service Port Reference

| Service | Port | Description |
|---|---|---|
| Frontend (Next.js) | 3000 | React UI |
| Gateway API | 8000 | FastAPI BFF — main backend |
| Ingestion Service | 8001 | Polls Athena, HealthGorilla, Pathway |
| Conflict Detection | 8003 | Rule-based conflict engine |
| AI Agent Service | 8004 | LangGraph agents (Clinical Summary, Med Recon, Lab Intel, Visit Prep) |
| Notification Service | 8006 | Microsoft Teams webhook |
| Mock HealthGorilla | 8081 | Synthetic FHIR R4 data |
| Mock Pathway | 8082 | Synthetic encounters and referrals |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Summary cache |

---

## Troubleshooting

### `psql: FATAL: password authentication failed`
Your `pg_hba.conf` requires scram-sha-256 but the password wasn't set. Run:
```sql
ALTER USER upv WITH PASSWORD 'upv';
```

### `pip install` fails with SSL error
Add trusted hosts:
```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <package>
```

### `npm install` fails with SSL error
```powershell
npm config set strict-ssl false
```

### Port already in use
```powershell
# Find and kill the process on a port (e.g. 8000)
Get-NetTCPConnection -LocalPort 8000 |
    Select-Object -ExpandProperty OwningProcess |
    ForEach-Object { Stop-Process -Id $_ -Force }
```

### Migration fails with `InFailedSqlTransaction`
A previous migration partially ran. Reset and retry:
```powershell
psql -U upv -d upv -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -U upv -d upv -c 'GRANT ALL ON SCHEMA public TO upv;'
cd migrations && alembic upgrade head
```

### AI summaries not generating
Expected — AI agent service requires valid `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`.  
The **demo page** (`/demo`) uses hardcoded synthetic data and works without any API keys.

### Kafka errors in logs
Kafka is not required for local dev. Services will log connection errors but continue working — conflict detection and AI agent triggers work on-demand via the API.

---

## What Runs Without External API Keys

| Feature | Without Keys | With Keys |
|---|---|---|
| Demo page (`/demo`) | ✅ Full UI + synthetic data | ✅ |
| Patient timeline | ✅ (from DB) | ✅ |
| Conflict detection | ✅ (rule engine only) | ✅ |
| AI summaries | ❌ (returns 404) | ✅ |
| Lab intelligence | ❌ (returns 404) | ✅ |
| Visit prep | ❌ (returns 404) | ✅ |
| Athena live data | ❌ | ✅ (with Athena credentials) |
| Teams notifications | ❌ | ✅ (with webhook URL) |

---

## Next Steps

- Add real `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` to `.env.local` for AI features
- Point `ATHENA_CLIENT_ID/SECRET/PRACTICE_ID` to a sandbox Athena account for live data
- See [deployment.md](./deployment.md) for AKS/Docker production deployment
