@echo off
chcp 65001 >nul
set "MX_KEY=%MX_APIKEY%"
if "%MX_KEY%"=="" (
    for /f "usebackq tokens=2*" %%A in (`reg query "HKCU\Environment" /v MX_APIKEY 2^>nul`) do set "MX_KEY=%%A"
    if "%MX_KEY%"=="" (
        for /f "usebackq tokens=2*" %%A in (`reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v MX_APIKEY 2^>nul`) do set "MX_KEY=%%A"
    )
)
python -X utf8 -u "C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\main.py" --exp quant_ml_v1
