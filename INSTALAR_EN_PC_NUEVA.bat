@echo off
:: ============================================================
::  INSTALAR EN PC NUEVA - Cobro Fácil POS
::  Ejecutar como ADMINISTRADOR
::  Extrae el ZIP, instala Python si falta, crea acceso directo
:: ============================================================
title Cobro Fácil POS - Instalador
color 0A
echo.
echo  ============================================
echo    CAJAFACIL PRO - INSTALADOR AUTOMATICO
echo  ============================================
echo.

set "ORIGEN=%~dp0"
set "DESTINO=C:\Cobro Fácil POS"

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
copy /Y "%ORIGEN%CobroFacil_POS.bat" "%DESTINO%\CobroFacil_POS.bat" > nul
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

:: ── PASO 5.5: Descargar e Instalar Herramientas de Hardware ──
echo.
echo  Descargando herramientas de hardware (RPT Tool y Drivers 3nStar)...
if not exist "%DESTINO%\utilidades_hardware" mkdir "%DESTINO%\utilidades_hardware"

echo  Descargando RPT Printer Tool...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/tools/RPT-Printer-Tool.zip' -OutFile '%DESTINO%\utilidades_hardware\RPT-Printer-Tool.zip'"
if exist "%DESTINO%\utilidades_hardware\RPT-Printer-Tool.zip" (
    echo  Extrayendo RPT Printer Tool...
    powershell -Command "Expand-Archive -Path '%DESTINO%\utilidades_hardware\RPT-Printer-Tool.zip' -DestinationPath '%DESTINO%\utilidades_hardware\RPT-Printer-Tool' -Force"
    del /f /q "%DESTINO%\utilidades_hardware\RPT-Printer-Tool.zip"
    if exist "%DESTINO%\utilidades_hardware\RPT-Printer-Tool\RPT-Printer-Tool" (
        xcopy "%DESTINO%\utilidades_hardware\RPT-Printer-Tool\RPT-Printer-Tool\*" "%DESTINO%\utilidades_hardware\RPT-Printer-Tool\" /E /Y /Q > nul
        rmdir /s /q "%DESTINO%\utilidades_hardware\RPT-Printer-Tool\RPT-Printer-Tool"
    )
    echo  [OK] RPT Printer Tool instalado
) else (
    echo  [!] Advertencia: No se pudo descargar RPT Printer Tool. Se descargara al usar la app.
)

echo  Descargando Drivers 3nStar...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/tools/3nStar-Drivers.zip' -OutFile '%DESTINO%\utilidades_hardware\3nStar-Drivers.zip'"
if exist "%DESTINO%\utilidades_hardware\3nStar-Drivers.zip" (
    echo  Extrayendo Drivers 3nStar...
    powershell -Command "Expand-Archive -Path '%DESTINO%\utilidades_hardware\3nStar-Drivers.zip' -DestinationPath '%DESTINO%\utilidades_hardware\3nStar-Drivers' -Force"
    del /f /q "%DESTINO%\utilidades_hardware\3nStar-Drivers.zip"
    if exist "%DESTINO%\utilidades_hardware\3nStar-Drivers\3nStar-Drivers" (
        xcopy "%DESTINO%\utilidades_hardware\3nStar-Drivers\3nStar-Drivers\*" "%DESTINO%\utilidades_hardware\3nStar-Drivers\" /E /Y /Q > nul
        rmdir /s /q "%DESTINO%\utilidades_hardware\3nStar-Drivers\3nStar-Drivers"
    )
    echo  [OK] Drivers 3nStar instalados
) else (
    echo  [!] Advertencia: No se pudo descargar Drivers 3nStar. Se descargaran al usar la app.
)

:: ── PASO 6: Crear acceso directo en escritorio ────────────────
echo.
echo  Creando acceso directo en escritorio...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Cobro Fácil POS.lnk'); $s.TargetPath = '%DESTINO%\CobroFacil_POS.bat'; $s.WorkingDirectory = '%DESTINO%'; $s.Description = 'Cobro Fácil POS - Sistema de Ventas'; $s.Save()" > nul
echo  [OK] Acceso directo creado en escritorio

:: ── LISTO ──────────────────────────────────────────────────────
echo.
echo  ============================================
echo    INSTALACION COMPLETADA!
echo.
echo    Doble clic en "Cobro Fácil POS" del escritorio
echo    para iniciar el sistema.
echo  ============================================
echo.
pause
