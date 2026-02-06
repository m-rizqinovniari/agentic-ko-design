@echo off
echo ========================================
echo Ko-Desain Platform - Local Setup
echo (Tanpa Docker - Cloud Database)
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan. Install Python 3.11+ terlebih dahulu.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js tidak ditemukan. Install Node.js 18+ terlebih dahulu.
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python dan Node.js ditemukan
echo.

echo [1/5] Membuat folder uploads...
if not exist "backend\uploads" mkdir backend\uploads
if not exist "backend\uploads\audio" mkdir backend\uploads\audio
echo Folder uploads dibuat.

echo.
echo [2/5] Membuat virtual environment Python...
cd backend
if not exist "venv" (
    python -m venv venv
    echo Virtual environment dibuat.
) else (
    echo Virtual environment sudah ada.
)

echo.
echo [3/5] Mengaktifkan venv dan install dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo.
echo [4/5] Install frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo ========================================
echo Setup Selesai!
echo ========================================
echo.
echo PENTING: Edit backend\.env dan masukkan:
echo   1. Supabase PostgreSQL credentials
echo   2. MongoDB Atlas connection string
echo   3. Upstash Redis URL
echo   4. Anthropic API Key
echo.
echo Lihat SETUP-CLOUD.md untuk panduan lengkap.
echo.
echo Untuk menjalankan aplikasi:
echo.
echo   Terminal 1 (Backend):
echo     cd backend
echo     venv\Scripts\activate
echo     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo   Terminal 2 (Frontend):
echo     cd frontend
echo     npm run dev
echo.
echo Akses:
echo   - Frontend: http://localhost:5173
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
pause
