@echo off
setlocal
cd /d "%~dp0"
python alass_gui.py
if errorlevel 1 (
  echo.
  echo Failed to start Alass GUI. Make sure Python 3 is installed and available as "python".
  echo If needed, install Python from https://www.python.org/downloads/windows/
  pause
)
