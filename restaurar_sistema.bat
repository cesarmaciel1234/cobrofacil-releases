@echo off
title Sistema de Restauracion PunPro 2026
color 0E

echo ===============================================================================
echo ⏪ RESTAURADOR DE EMERGENCIA - PUNPRO 2026
echo ===============================================================================
echo.

:: 1. Buscar la carpeta de backup mas reciente
set "LATEST_BACKUP="
for /f "delims=" %%a in ('dir /b /ad /o-n backups\Respaldo_* 2^>nul') do (
    set "LATEST_BACKUP=backups\%%a"
    goto :found
)

:found
if "%LATEST_BACKUP%"=="" (
    color 0C
    echo [ERROR] No se encontraron carpetas de respaldo en 'backups/'.
    echo Primero debes ejecutar 'backup_total.bat' para crear un punto de restauracion.
    echo.
    pause
    exit /b
)

echo [INFO] Se ha detectado el respaldo mas reciente en:
echo --^> %LATEST_BACKUP%
echo.
echo [ADVERTENCIA] Al continuar, se sobreescribira la base de datos y configuracion
echo actual con los datos del respaldo. Los datos actuales se perderan.
echo.
set /p confirm="¿Estas seguro de que deseas restaurar? (S/N): "

if /i "%confirm%" neq "S" (
    echo.
    echo Operacion cancelada por el usuario.
    pause
    exit /b
)

:: 2. Proceso de restauracion
echo.
echo [1/2] Restaurando Base de Datos...
if exist "%LATEST_BACKUP%\datos_criticos\punpro.db" (
    copy /y "%LATEST_BACKUP%\datos_criticos\punpro.db" "punpro.db" >nul
    echo      OK.
) else (
    echo      [ERROR] No se encontro punpro.db en el respaldo.
)

echo [2/2] Restaurando Configuracion...
if exist "%LATEST_BACKUP%\datos_criticos\config.json" (
    copy /y "%LATEST_BACKUP%\datos_criticos\config.json" "config.json" >nul
    echo      OK.
) else (
    echo      [ERROR] No se encontro config.json en el respaldo.
)

echo.
echo ===============================================================================
echo ✅ SISTEMA RESTAURADO CON EXITO
echo ===============================================================================
echo.
echo Ya puedes iniciar el programa normalmente.
pause
