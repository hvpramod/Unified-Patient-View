@echo off
echo Starting Unified Patient View — All Services
echo ============================================

SET ROOT=F:\UnifiedPatienntView
SET VENV=%ROOT%\.venv\Scripts
SET DB=postgresql+asyncpg://upv:upv@localhost:5432/upv
SET REDIS=redis://localhost:6379
SET KAFKA=localhost:9092

:: Start Redis
echo [Redis] Starting...
start "Redis" /min "C:\Program Files\Redis\redis-server.exe"
timeout /t 2 /nobreak >nul

:: Mock HealthGorilla
echo [Mock HealthGorilla] Starting on port 8081...
start "Mock HealthGorilla" /min /d "%ROOT%\mocks\healthgorilla" cmd /c "set DATABASE_URL=%DB%&& set REDIS_URL=%REDIS%&& %VENV%\uvicorn.exe main:app --host 0.0.0.0 --port 8081"

:: Mock Pathway
echo [Mock Pathway] Starting on port 8082...
start "Mock Pathway" /min /d "%ROOT%\mocks\pathway" cmd /c "set DATABASE_URL=%DB%&& %VENV%\uvicorn.exe main:app --host 0.0.0.0 --port 8082"

timeout /t 3 /nobreak >nul

:: Gateway API
echo [Gateway API] Starting on port 8000...
start "UPV Gateway API" /d "%ROOT%\apps\gateway-api" cmd /c "set DATABASE_URL=%DB%&& set REDIS_URL=%REDIS%&& set AZURE_TENANT_ID=&& set AZURE_CLIENT_ID=&& set AI_AGENT_SERVICE_URL=http://localhost:8004&& %VENV%\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Ingestion Service
echo [Ingestion] Starting on port 8001...
start "UPV Ingestion" /min /d "%ROOT%\apps\ingestion-service" cmd /c "set DATABASE_URL=%DB%&& set KAFKA_BOOTSTRAP_SERVERS=%KAFKA%&& set HEALTHGORILLA_BASE_URL=http://localhost:8081&& set PATHWAY_BASE_URL=http://localhost:8082&& set ATHENA_POLL_INTERVAL_SECONDS=3600&& %VENV%\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001"

:: Conflict Detection
echo [Conflict Detection] Starting on port 8003...
start "UPV Conflict" /min /d "%ROOT%\apps\conflict-detection" cmd /c "set DATABASE_URL=%DB%&& set KAFKA_BOOTSTRAP_SERVERS=%KAFKA%&& %VENV%\uvicorn.exe app.main:app --host 0.0.0.0 --port 8003"

:: AI Agent Service
echo [AI Agents] Starting on port 8004...
start "UPV AI Agents" /min /d "%ROOT%\apps\ai-agent-service" cmd /c "set DATABASE_URL=%DB%&& set REDIS_URL=%REDIS%&& set KAFKA_BOOTSTRAP_SERVERS=%KAFKA%&& set OPENAI_API_KEY=sk-placeholder&& set ANTHROPIC_API_KEY=sk-ant-placeholder&& %VENV%\uvicorn.exe app.main:app --host 0.0.0.0 --port 8004"

:: Notification Service
echo [Notifications] Starting on port 8006...
start "UPV Notifications" /min /d "%ROOT%\apps\notification-service" cmd /c "set KAFKA_BOOTSTRAP_SERVERS=%KAFKA%&& set AI_AGENT_SERVICE_URL=http://localhost:8004&& %VENV%\uvicorn.exe app.main:app --host 0.0.0.0 --port 8006"

:: Frontend (Next.js)
echo [Frontend] Starting on port 3000...
start "UPV Frontend" /d "%ROOT%\apps\frontend" cmd /c "set NEXT_PUBLIC_API_URL=http://localhost:8000&& npm run dev"

echo.
echo ============================================
echo All services launching...
echo Wait ~15 seconds then open:
echo.
echo   http://localhost:3000/demo    (Full UI - no login)
echo   http://localhost:8000/api/docs (API Swagger)
echo   http://localhost:8000/health   (API health)
echo ============================================
echo.
echo To stop: close the individual service windows
echo or run stop-all.bat
pause
