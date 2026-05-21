@echo off
:: ============================================================
::  CajaFacil Pro - Compilador del Instalador
::  Genera: CajaFacil_Pro_Setup.exe + CajaFacil_Pro_Setup.zip
::  Ejecutar desde la carpeta raiz del proyecto
:: ============================================================
title CajaFacil Pro - Compilando Instalador...
color 0B
echo.
echo  =============================================
echo   CAJAFACIL PRO - GENERADOR DE INSTALADOR
echo  =============================================
echo.

:: Verificar que estamos en la raiz del proyecto
if not exist "main.py" (
    echo  [ERROR] Ejecutar desde la carpeta raiz del proyecto
    echo  No ejecutar desde dentro de la carpeta installer\
    pause & exit /b 1
)

:: Limpiar builds anteriores
echo  Limpiando builds anteriores...
if exist "dist_installer"  rmdir /s /q "dist_installer"
if exist "build_installer" rmdir /s /q "build_installer"
if exist "CajaFacil_Pro_Setup.exe" del /f /q "CajaFacil_Pro_Setup.exe"
if exist "CajaFacil_Pro_Setup.zip" del /f /q "CajaFacil_Pro_Setup.zip"

:: Compilar con PyInstaller
echo  Compilando instalador...
echo  (Puede tardar 1-2 minutos)
echo.
.\.venv\Scripts\pyinstaller.exe ^
    --onefile ^
    --windowed ^
    --name "CajaFacil_Pro_Setup" ^
    --distpath ".\dist_installer" ^
    --workpath ".\build_installer" ^
    --specpath ".\build_installer" ^
    installer\installer_build.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Fallo la compilacion. Revisa el log arriba.
    pause & exit /b 1
)

:: Empaquetar en ZIP
echo.
echo  Empaquetando en ZIP...
powershell -Command "Compress-Archive -Path 'dist_installer\CajaFacil_Pro_Setup.exe' -DestinationPath 'CajaFacil_Pro_Setup.zip' -Force"

:: Limpiar temporales de build
rmdir /s /q "dist_installer"  2>nul
rmdir /s /q "build_installer" 2>nul

:: Resultado
echo.
for %%F in ("CajaFacil_Pro_Setup.zip") do set SIZE=%%~zF
set /a SIZEMB=%SIZE:~0,-3%
echo  =============================================
echo   LISTO!
echo.
echo   Archivo generado: CajaFacil_Pro_Setup.zip
echo   Compartir este ZIP con los clientes
echo  =============================================
echo.
pause
