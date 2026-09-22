@echo off
REM Double-click this file. Nothing else is needed -- not even Python.
REM It runs unattended; leave it alone until it says it has finished.
title Enron ILI pipeline - setup
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1" %*
echo.
if errorlevel 1 (
  echo ============================================================
  echo  SETUP DID NOT COMPLETE.
  echo  Send bootstrap-report.json ^(in this folder^) to Jez.
  echo ============================================================
) else (
  echo ============================================================
  echo  SETUP COMPLETE. Your environment is verified.
  echo ============================================================
)
echo.
pause
