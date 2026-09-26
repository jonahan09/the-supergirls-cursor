@echo off
setlocal
cd /d "%~dp0"
title Crear EXE - SuperGirls Pet v11

where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3"
) else (
    set "PY=python"
)

echo Instalando/actualizando PyInstaller y PyQt6...
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo.
echo Creando ejecutable para Windows...
%PY% -m PyInstaller --noconfirm --clean --windowed --name "SuperGirls Pet v11" --add-data "skins;skins" --add-data "skins.json;." supergirls_pet.py
if errorlevel 1 goto :error

echo.
echo LISTO.
echo El programa queda en:
echo   dist\SuperGirls Pet v11\SuperGirls Pet v11.exe
echo.
pause
exit /b 0

:error
echo.
echo Ocurrio un error creando el EXE.
echo Revisa que Python este instalado y tenga acceso a Internet para instalar dependencias.
pause
exit /b 1
