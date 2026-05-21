@echo off
:: ============================================================
::  INSTALAR EN PC NUEVA - CajaFacil Pro
::  Ejecutar como ADMINISTRADOR
::  Extrae el ZIP, instala Python si falta, crea acceso directo
:: ============================================================
title CajaFacil Pro - Instalador
color 0A
echo.
echo  ============================================
echo    CAJAFACIL PRO - INSTALADOR AUTOMATICO
echo  ============================================
echo.

set "ORIGEN=%~dp0"
set "DESTINO=C:\CajaFacil Pro"

echo  Destino: %DESTINO%
echo.

:: ── PASO 1: Crear carpeta destino ─────────────────────────────
if not exist "%DESTINO%" (
    mkdir "%DESTINO%"
    echo  [OK] Carpeta creada
) else (
    echo  [OK] Carpeta ya existe, actualizando...
)

:: ── PASO 2: Copiar archivos del sistema ───────────────────────
echo  Copiando archivos...
xcopy "%ORIGEN%src"         "%DESTINO%\src"  /E /Y /Q > nul
copy /Y "%ORIGEN%main.py"           "%DESTINO%\main.py"          > nul
copy /Y "%ORIGEN%version.json"      "%DESTINO%\version.json"     > nul
copy /Y "%ORIGEN%requirements.txt"  "%DESTINO%\requirements.txt" > nul
copy /Y "%ORIGEN%CajaFacil_Pro.bat" "%DESTINO%\CajaFacil_Pro.bat" > nul
copy /Y "%ORIGEN%ACTUALIZAR.bat"    "%DESTINO%\ACTUALIZAR.bat"   > nul

:: Copiar config.json solo si NO existe (no pisar configuracion del cliente)
if not exist "%DESTINO%\config.json" (
    copy /Y "%ORIGEN%config.json" "%DESTINO%\config.json" > nul
    echo  [OK] Configuracion inicial copiada
) else (
    echo  [OK] Configuracion existente conservada
)

:: Copiar DB solo si NO existe
if not exist "%DESTINO%\punpro.db" (
    if exist "%ORIGEN%punpro.db" (
        copy /Y "%ORIGEN%punpro.db" "%DESTINO%\punpro.db" > nul
        echo  [OK] Base de datos nueva creada
    )
) else (
    echo  [OK] Base de datos existente conservada
)

:: Crear carpetas necesarias
mkdir "%DESTINO%\logs"       2>nul
mkdir "%DESTINO%\reportes"   2>nul
mkdir "%DESTINO%\backups"    2>nul
mkdir "%DESTINO%\certificados" 2>nul
echo  [OK] Carpetas del sistema listas

:: ── PASO 3: Verificar Python ───────────────────────────────────
echo.
echo  Verificando Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo  [!] Python no encontrado. Descargando instalador...
    echo      Esto puede tardar unos minutos con internet...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    echo  [!] Instalando Python (sin interaccion)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
    echo  [OK] Python instalado
) else (
    echo  [OK] Python ya instalado
)

:: ── PASO 4: Crear entorno virtual e instalar dependencias ─────
echo.
echo  Creando entorno virtual...
if not exist "%DESTINO%\.venv" (
    python -m venv "%DESTINO%\.venv"
    echo  [OK] Entorno virtual creado
) else (
    echo  [OK] Entorno virtual ya existe
)

echo  Instalando dependencias (puede tardar 2-3 minutos)...
"%DESTINO%\.venv\Scripts\pip.exe" install --quiet --upgrade pip > nul
"%DESTINO%\.venv\Scripts\pip.exe" install --quiet -r "%DESTINO%\requirements.txt"
echo  [OK] Dependencias instaladas

:: ── PASO 5: Limpiar config de rutas del desarrollador ─────────
"%DESTINO%\.venv\Scripts\python.exe" -c "
import json
cfg = r'%DESTINO%\config.json'
with open(cfg, 'r', encoding='utf-8') as f:
    d = json.load(f)
d['db_path'] = ''
with open(cfg, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=4, ensure_ascii=False)
" 2>nul
echo  [OK] Configuracion limpiada

:: ── PASO 6: Crear acceso directo en escritorio ────────────────
echo.
echo  Creando acceso directo en escritorio...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\CajaFacil Pro.lnk'); $s.TargetPath = '%DESTINO%\CajaFacil_Pro.bat'; $s.WorkingDirectory = '%DESTINO%'; $s.Description = 'CajaFacil Pro - Sistema de Ventas'; $s.Save()" > nul
echo  [OK] Acceso directo creado en escritorio

:: ── LISTO ──────────────────────────────────────────────────────
echo.
echo  ============================================
echo    INSTALACION COMPLETADA!
echo.
echo    Doble clic en "CajaFacil Pro" del escritorio
echo    para iniciar el sistema.
echo  ============================================
echo.
pause
