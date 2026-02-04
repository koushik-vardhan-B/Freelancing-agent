@echo off
REM ============================================
REM CLEAN INSTALL SCRIPT
REM Run this if your venv is broken
REM ============================================

echo.
echo ========================================
echo CLEANING AND REINSTALLING ENVIRONMENT
echo ========================================
echo.

REM Deactivate if active
call deactivate 2>nul

REM Remove old venv
echo Removing old .venv...
rmdir /s /q .venv 2>nul

REM Create new venv
echo Creating new virtual environment...
python -m venv .venv

REM Activate
echo Activating...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install playwright langgraph langchain-core jsonpatch groq openpyxl python-dotenv loguru

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium

echo.
echo ========================================
echo DONE! Now test with:
echo   python test_playwright.py
echo   python test_langgraph.py
echo ========================================
echo.

pause
