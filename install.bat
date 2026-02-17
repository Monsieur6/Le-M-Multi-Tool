@echo off
title Installing Dependencies...
echo Installing Python libraries from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo An error occurred during installation.
    pause
    exit /b %errorlevel%
)
echo.
echo Installation complete!
pause
