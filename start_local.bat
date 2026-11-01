@echo off
title AI Real Estate Deal Analyzer - Launcher
cls

echo =================================================================
echo    AI REAL ESTATE DEAL ANALYZER (INDIA) - WINDOWS 11 LAUNCHER
echo =================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_local.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Launcher encountered an issue. See details above.
    pause
)

