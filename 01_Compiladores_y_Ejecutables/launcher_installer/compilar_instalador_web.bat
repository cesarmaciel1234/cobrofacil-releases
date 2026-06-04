@echo off
setlocal enabledelayedexpansion
title Compilador - Instalador Web / Launcher
color 1F

echo ==========================================================
echo 🚀 COMPILANDO EL INSTALADOR MODULAR TIPO LAUNCHER
echo ==========================================================
echo.

if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
)

:: Garantizar que PyInstaller y dependencias de Windows esten
pip install pyinstaller pywin32 PyQt5 >nul 2>&1

:: Limpiar basuras
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Construyendo un Setup.exe ultra ligero (Un solo archivo)...
pyinstaller --noconfirm --onefile --windowed ^
  --name "Setup_CobroFacil_Web" ^
  --hidden-import "win32com" ^
  --hidden-import "win32com.client" ^
  --icon=NONE ^
  --add-data "web;web" ^
  Instalador_Web.py

echo.
echo ==========================================================
echo ✅ COMPILACION TERMINADA
echo ==========================================================
echo El instalador ha sido generado en la carpeta:
echo launcher_installer\dist\Setup_CobroFacil_Web.exe
echo.
:: pause
