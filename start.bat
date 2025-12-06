@echo off
REM ROS-GUI Windows Quick Start Script

echo ====================================
echo   ROS-GUI Platform - Quick Start
echo ====================================
echo.

REM Check if in project root
if not exist "frontend\" (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist "backend\" (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

REM Start Backend
echo [1/2] Starting Backend...
cd backend

REM Check Python virtual environment
if not exist "venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist ".deps_installed" (
    echo Installing backend dependencies...
    pip install -r requirements.txt
    echo. > .deps_installed
)

REM Run database migrations
echo Running database migrations...
alembic upgrade head 2>nul || echo Warning: Skipping migrations

REM Start backend server
echo Starting backend server...
start "ROS-GUI Backend" cmd /k "python -m backend.server"

cd ..

REM Start Frontend
echo.
echo [2/2] Starting Frontend...
cd frontend

REM Check node_modules
if not exist "node_modules\" (
    echo Installing frontend dependencies...
    call npm install
)

REM Start frontend dev server
echo Starting frontend dev server...
start "ROS-GUI Frontend" cmd /k "npm run dev"

cd ..

echo.
echo ====================================
echo   ROS-GUI Platform is running!
echo ====================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to open frontend in browser...
pause >nul

start http://localhost:5173

echo.
echo To stop services, close the terminal windows
echo.
pause

