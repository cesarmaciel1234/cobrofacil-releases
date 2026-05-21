@echo off
title Sistema de Respaldo PunPro 2026 - Recuperacion Total
color 0A

echo ===============================================================================
echo 🛡️ INICIANDO RESPALDO DE SEGURIDAD ABSOLUTO - PUNPRO 2026
echo ===============================================================================
echo.

:: 1. Crear carpetas de respaldo con marca de tiempo
set "TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_DIR=backups\Respaldo_%TIMESTAMP%"

echo [1/3] Creando boveda de seguridad en %BACKUP_DIR%...
mkdir "%BACKUP_DIR%" 2>nul
mkdir "%BACKUP_DIR%\datos_criticos" 2>nul

:: 2. Respaldar archivos de datos (lo mas importante)
echo [2/3] Copiando base de datos y configuracion...
if exist "punpro.db" copy /y "punpro.db" "%BACKUP_DIR%\datos_criticos\punpro.db" >nul
if exist "config.json" copy /y "config.json" "%BACKUP_DIR%\datos_criticos\config.json" >nul
if exist "crash.log" copy /y "crash.log" "%BACKUP_DIR%\datos_criticos\crash.log" >nul

:: 3. Generar ZIP completo del codigo fuente (excluyendo basura de compilacion)
echo [3/3] Comprimiendo TODO el proyecto para respaldo total...
echo (Esto puede tardar un momento, estamos sellando el corazon del sistema)

powershell.exe -nologo -noprofile -command "Compress-Archive -Path 'main.py', 'src', 'docs', 'requirements.txt', '*.iss', '*.bat', 'punpro.db', 'config.json' -DestinationPath 'PROYECTO_COMPLETO_RESPALDO.zip' -Force"

echo.
echo ===============================================================================
echo ✅ PROCESO DE RESPALDO FINALIZADO CON EXITO
echo ===============================================================================
echo.
echo Se ha generado:
echo 1. Carpeta de boveda: %BACKUP_DIR%
echo 2. Archivo maestro: PROYECTO_COMPLETO_RESPALDO.zip
echo.
echo Ya puedes proceder con la compilacion final con seguridad total.
pause
