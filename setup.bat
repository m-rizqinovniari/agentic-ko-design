@echo off
echo ========================================
echo Ko-Desain Platform Setup
echo ========================================
echo.

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [1/5] Creating .env files...

:: Backend .env
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env"
    echo Created backend\.env - Please edit and add your ANTHROPIC_API_KEY
) else (
    echo backend\.env already exists
)

:: Frontend .env
if not exist "frontend\.env" (
    copy "frontend\.env.example" "frontend\.env"
    echo Created frontend\.env
) else (
    echo frontend\.env already exists
)

echo.
echo [2/5] Starting Docker services (PostgreSQL, MongoDB, Redis)...
docker-compose up -d postgres mongodb redis

echo.
echo [3/5] Waiting for databases to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [4/5] Building and starting backend...
docker-compose up -d --build backend

echo.
echo [5/5] Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo IMPORTANT: Before running, edit backend\.env and add your ANTHROPIC_API_KEY
echo.
echo To start the application:
echo   1. Backend is already running at http://localhost:8000
echo   2. Run frontend: cd frontend ^&^& npm run dev
echo.
echo API Documentation: http://localhost:8000/docs
echo.
pause
