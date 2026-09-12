@echo off
rem Starts the web app for local development (Windows). Requires Node.js 22: https://nodejs.org
cd /d "%~dp0web"
where npm >nul 2>nul || (echo Node.js 22 is required: https://nodejs.org & pause & exit /b 1)
if not exist node_modules call npm install
echo Site: http://localhost:3000  (Ctrl+C to stop)
call npm run dev
pause
