@echo off
echo Starting Ko-Desain Backend...
cd backend
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
