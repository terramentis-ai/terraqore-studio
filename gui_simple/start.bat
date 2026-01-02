@echo off
REM TerraQore Streamlit UI Launcher
REM Run this to start the non-technical UI

echo.
echo ==================================================
echo    TerraQore Studio - Non-Technical UI
echo ==================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo [INFO] Activating virtual environment...
    call ..\..\.venv\Scripts\activate.bat
)

echo [INFO] Starting Streamlit UI...
echo [INFO] Access UI at: http://localhost:8501
echo.

streamlit run app.py --server.port=8501 --server.address=localhost

pause
