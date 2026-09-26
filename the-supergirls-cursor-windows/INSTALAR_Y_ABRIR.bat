@echo off
setlocal
cd /d "%~dp0"
title SuperGirls Pet v11 - Instalador Windows

echo ==============================================
echo       SuperGirls Pet v11 - Windows
echo ==============================================
echo.

where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3"
    set "PYW=pyw -3"
    goto :python_ok
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PY=python"
    set "PYW=pythonw"
    goto :python_ok
)

echo No se encontro Python.
echo.
echo Instala Python 3.11, 3.12 o 3.13 para Windows y marca:
echo     Add python.exe to PATH
echo Luego vuelve a abrir este archivo.
echo.
pause
exit /b 1

:python_ok
echo Comprobando PyQt6...
%PY% -c "import PyQt6" >nul 2>nul
if errorlevel 1 (
    echo PyQt6 no esta instalado. Instalando...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo No se pudo instalar PyQt6.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando SuperGirls Pet...
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

%PY% "%~dp0supergirls_pet.py"
