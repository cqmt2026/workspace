@echo off
chcp 65001 >nul 2>&1
set MX_KEY=%MX_APIKEY%
python "%~dp0mx_realtime_warmup.py"
