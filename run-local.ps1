# ── UPV Local Run Script ────────────────────────────────────────────────────
# Starts all services locally without Docker
# Usage: .\run-local.ps1
# Stop all: Get-Job | Stop-Job; Get-Job | Remove-Job

$root    = "F:\UnifiedPatienntView"
$venv    = "$root\.venv\Scripts"
$python  = "$venv\python.exe"
$uvicorn = "$venv\uvicorn.exe"

# Shared environment
$env:DATABASE_URL            = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
$env:REDIS_URL               = "redis://localhost:6379"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
$env:AZURE_TENANT_ID         = ""
$env:AZURE_CLIENT_ID         = ""
$env:OPENAI_API_KEY          = $env:OPENAI_API_KEY ?? "sk-placeholder"
$env:ANTHROPIC_API_KEY       = $env:ANTHROPIC_API_KEY ?? "sk-ant-placeholder"
$env:NEXT_PUBLIC_API_URL     = "http://localhost:8000"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  UPV — Starting All Services Locally" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# ── 1. Redis ─────────────────────────────────────────────────────────────────
$redisCli = "C:\Program Files\Redis\redis-cli.exe"
$ping = & $redisCli ping 2>$null
if ($ping -ne "PONG") {
    Write-Host "[Redis] Starting..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Redis\redis-server.exe" -WindowStyle Hidden
    Start-Sleep 2
} else {
    Write-Host "[Redis] Already running ✓" -ForegroundColor Green
}

# ── 2. Mock services ─────────────────────────────────────────────────────────
Write-Host "[Mock HealthGorilla] Starting on :8081..." -ForegroundColor Yellow
Start-Job -Name "mock-healthgorilla" -ScriptBlock {
    $env:PYTHONPATH = ""
    Set-Location "F:\UnifiedPatienntView\mocks\healthgorilla"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8081
} | Out-Null

Write-Host "[Mock Pathway] Starting on :8082..." -ForegroundColor Yellow
Start-Job -Name "mock-pathway" -ScriptBlock {
    Set-Location "F:\UnifiedPatienntView\mocks\pathway"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8082
} | Out-Null

Start-Sleep 2

# ── 3. Ingestion service ──────────────────────────────────────────────────────
Write-Host "[Ingestion] Starting on :8001..." -ForegroundColor Yellow
Start-Job -Name "ingestion-service" -ScriptBlock {
    $env:DATABASE_URL            = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    $env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    $env:HEALTHGORILLA_BASE_URL  = "http://localhost:8081"
    $env:PATHWAY_BASE_URL        = "http://localhost:8082"
    $env:ATHENA_POLL_INTERVAL_SECONDS = "3600"
    Set-Location "F:\UnifiedPatienntView\apps\ingestion-service"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8001
} | Out-Null

# ── 4. Conflict detection ─────────────────────────────────────────────────────
Write-Host "[Conflict Detection] Starting on :8003..." -ForegroundColor Yellow
Start-Job -Name "conflict-detection" -ScriptBlock {
    $env:DATABASE_URL            = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    $env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    Set-Location "F:\UnifiedPatienntView\apps\conflict-detection"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8003
} | Out-Null

# ── 5. AI Agent service ───────────────────────────────────────────────────────
Write-Host "[AI Agents] Starting on :8004..." -ForegroundColor Yellow
Start-Job -Name "ai-agent-service" -ScriptBlock {
    $env:DATABASE_URL            = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    $env:REDIS_URL               = "redis://localhost:6379"
    $env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    $env:OPENAI_API_KEY          = $env:OPENAI_API_KEY
    $env:ANTHROPIC_API_KEY       = $env:ANTHROPIC_API_KEY
    Set-Location "F:\UnifiedPatienntView\apps\ai-agent-service"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8004
} | Out-Null

# ── 6. Gateway API ────────────────────────────────────────────────────────────
Write-Host "[Gateway API] Starting on :8000..." -ForegroundColor Yellow
Start-Job -Name "gateway-api" -ScriptBlock {
    $env:DATABASE_URL            = "postgresql+asyncpg://upv:upv@localhost:5432/upv"
    $env:REDIS_URL               = "redis://localhost:6379"
    $env:AI_AGENT_SERVICE_URL    = "http://localhost:8004"
    $env:INGESTION_SERVICE_URL   = "http://localhost:8001"
    $env:AZURE_TENANT_ID         = ""
    $env:AZURE_CLIENT_ID         = ""
    Set-Location "F:\UnifiedPatienntView\apps\gateway-api"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 --reload
} | Out-Null

# ── 7. Notification service ───────────────────────────────────────────────────
Write-Host "[Notifications] Starting on :8006..." -ForegroundColor Yellow
Start-Job -Name "notification-service" -ScriptBlock {
    $env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    $env:AI_AGENT_SERVICE_URL    = "http://localhost:8004"
    Set-Location "F:\UnifiedPatienntView\apps\notification-service"
    & "F:\UnifiedPatienntView\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8006
} | Out-Null

# ── 8. Frontend ───────────────────────────────────────────────────────────────
Write-Host "[Frontend] Starting on :3000..." -ForegroundColor Yellow
Start-Job -Name "frontend" -ScriptBlock {
    $env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
    Set-Location "F:\UnifiedPatienntView\apps\frontend"
    & npm run dev
} | Out-Null

# ── Wait and report ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep 8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Checking service health..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$services = @(
    @{ name="Gateway API";          url="http://localhost:8000/health" },
    @{ name="Ingestion Service";    url="http://localhost:8001/health" },
    @{ name="Conflict Detection";   url="http://localhost:8003/health" },
    @{ name="AI Agent Service";     url="http://localhost:8004/health" },
    @{ name="Notification Service"; url="http://localhost:8006/health" },
    @{ name="Mock HealthGorilla";   url="http://localhost:8081/health" },
    @{ name="Mock Pathway";         url="http://localhost:8082/health" },
    @{ name="Frontend";             url="http://localhost:3000/" }
)

foreach ($svc in $services) {
    try {
        $resp = Invoke-WebRequest -Uri $svc.url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        Write-Host "  $($svc.name.PadRight(25)) ✓  $($svc.url)" -ForegroundColor Green
    } catch {
        Write-Host "  $($svc.name.PadRight(25)) ○  starting... ($($svc.url))" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  UPV is running!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Demo page (no login):  http://localhost:3000/demo" -ForegroundColor White
Write-Host "  API Swagger docs:       http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "  API health:             http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "  To stop all services:  Get-Job | Stop-Job" -ForegroundColor Gray
Write-Host "  To view logs:          Receive-Job -Name gateway-api -Keep" -ForegroundColor Gray
Write-Host ""
