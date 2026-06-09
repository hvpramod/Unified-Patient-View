@echo off
echo Stopping all UPV services...
taskkill /FI "WINDOWTITLE eq UPV*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Mock*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Redis*" /F >nul 2>&1

:: Kill ports
for %%p in (8000 8001 8003 8004 8006 8081 8082) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| find ":%%p "') do taskkill /PID %%a /F >nul 2>&1
)

echo All services stopped.
