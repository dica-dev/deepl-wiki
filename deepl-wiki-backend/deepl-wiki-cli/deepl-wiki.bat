@echo off
REM DeepL Wiki CLI launcher script
cd /d "%~dp0"
python -m cli.main %*
