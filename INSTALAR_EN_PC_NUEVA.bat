@echo off
:: ============================================================
::  INSTALADOR CAJAFACIL PRO
::  Ejecutar como ADMINISTRADOR en la PC nueva
::  Copia todos los archivos y crea acceso directo en escritorio
:: ============================================================
title Instalador CajaFacil Pro
color 0A
echo.
echo  ========================================
echo   CAJAFACIL PRO - INSTALADOR AUTOMATICO
echo  ========================================
echo.

:: Detectar ruta del servidor (donde esta este instalador)
set "ORIGEN=%~dp0"
set "DESTINO=C:\CajaFacil Pro"

echo  Origen : %ORIGEN%
echo  Destino: %DESTINO%
echo.

:: Crear carpeta destino
if not exist "%DESTINO%" (
    mkdir "%DESTINO%"
    echo  [OK] Carpeta creada: %DESTINO%
) else (
    echo  [OK] Carpeta ya existe, actualizando...
)

:: Copiar todos los archivos (excepto la DB si ya existe)
echo.
echo  Copiando archivos del sistema...
xcopy "%ORIGEN%src" "%DESTINO%\src" /E /Y /Q > nul
xcopy "%ORIGEN%.venv" "%DESTINO%\.venv" /E /Y /Q > nul
copy /Y "%ORIGEN%main.py" "%DESTINO%\main.py" > nul
copy /Y "%ORIGEN%config.json" "%DESTINO%\config.json" > nul
copy /Y "%ORIGEN%version.json" "%DESTINO%\version.json" > nul
copy /Y "%ORIGEN%CajaFacil_Pro.bat" "%DESTINO%\CajaFacil_Pro.bat" > nul

:: Copiar DB solo si NO existe (no pisar datos del cliente)
if not exist "%DESTINO%\punpro.db" (
    copy /Y "%ORIGEN%punpro.db" "%DESTINO%\punpro.db" > nul
    echo  [OK] Base de datos nueva creada
) else (
    echo  [OK] Base de datos existente conservada (no se sobreescribio)
)

:: Crear carpetas necesarias
mkdir "%DESTINO%\logs" 2>nul
mkdir "%DESTINO%\reportes" 2>nul
mkdir "%DESTINO%\backups" 2>nul
mkdir "%DESTINO%\certificados" 2>nul
echo  [OK] Carpetas del sistema creadas

:: Limpiar config.json de rutas del desarrollador
"%DESTINO%\.venv\Scripts\python.exe" -c "
import json, os
cfg = r'%DESTINO%\config.json'
with open(cfg, 'r', encoding='utf-8') as f:
    d = json.load(f)
d['db_path'] = ''
with open(cfg, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=4, ensure_ascii=False)
print('[OK] config.json limpiado de rutas personales')
" 2>nul

:: Crear acceso directo en escritorio
echo.
echo  Creando acceso directo en escritorio...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\CajaFacil Pro.lnk'); $s.TargetPath = '%DESTINO%\CajaFacil_Pro.bat'; $s.WorkingDirectory = '%DESTINO%'; $s.Description = 'CajaFacil Pro'; $s.Save()" > nul
echo  [OK] Acceso directo creado en escritorio

echo.
echo  ========================================
echo   INSTALACION COMPLETADA!
echo   Doble clic en "CajaFacil Pro" del escritorio
echo  ========================================
echo.
pause
