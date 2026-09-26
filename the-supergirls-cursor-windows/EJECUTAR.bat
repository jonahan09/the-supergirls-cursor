@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if not errorlevel 1 (
    start "" pyw -3 "%~dp0supergirls_pet.py"
    exit /b 0
)

where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw "%~dp0supergirls_pet.py"
    exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0supergirls_pet.py"
    exit /b %errorlevel%
)

python "%~dp0supergirls_pet.py"
