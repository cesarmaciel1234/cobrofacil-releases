@echo off
:: ============================================================
::  ACTUALIZADOR CAJAFACIL PRO - PARA CLIENTES
::  Descargar el paquete .zip, extraer y ejecutar este archivo
::  Actualiza sin pisar la base de datos ni la configuracion
:: ============================================================
title Actualizador CajaFacil Pro
color 0A
echo.
echo  ========================================
echo   CAJAFACIL PRO - ACTUALIZADOR
echo  ========================================
echo.

set "ORIGEN=%~dp0"
set "DESTINO=C:\CajaFacil Pro"

:: Verificar que la app no este abierta
tasklist /fi "imagename eq pythonw.exe" 2>nul | find /i "pythonw.exe" >nul
if not errorlevel 1 (
    echo  ATENCION: El programa esta abierto. Cerralo antes de actualizar.
    echo.
    echo  Podes cerrarlo desde la app con Cerrar Sesion + cerrar ventana,
    echo  o desde el Administrador de Tareas buscando "pythonw.exe"
    echo.
    pause
    exit /b 1
)

:: Verificar que ya este instalado
if not exist "%DESTINO%\main.py" (
    echo  No se encontro instalacion en %DESTINO%
    echo  Ejecuta INSTALAR_EN_PC_NUEVA.bat primero.
    pause
    exit /b 1
)

echo  Instalacion encontrada en: %DESTINO%
echo  Actualizando archivos del sistema...
echo.

:: Copiar SOLO archivos del sistema (NO la DB, NO el config)
xcopy "%ORIGEN%src" "%DESTINO%\src" /E /Y /Q
copy /Y "%ORIGEN%main.py" "%DESTINO%\main.py" > nul
copy /Y "%ORIGEN%version.json" "%DESTINO%\version.json" > nul

echo  [OK] Archivos del sistema actualizados

:: Actualizar config solo si hay claves NUEVAS (sin pisar las del cliente)
echo  Verificando configuracion...
"%DESTINO%\.venv\Scripts\python.exe" -c "
import json, os

cfg_nuevo = r'%ORIGEN%config.json'
cfg_cliente = r'%DESTINO%\config.json'

# Leer config del paquete nuevo
with open(cfg_nuevo, 'r', encoding='utf-8') as f:
    nuevo = json.load(f)

# Leer config del cliente (si existe)
cliente = {}
if os.path.exists(cfg_cliente):
    try:
        with open(cfg_cliente, 'r', encoding='utf-8') as f:
            cliente = json.load(f)
    except:
        pass

# Solo agregar claves NUEVAS que no tenia el cliente (sin pisar sus datos)
claves_protegidas = {
    'business_name', 'business_cuit', 'address', 'phone',
    'db_path', 'mp_access_token', 'ticket_printer',
    'ticket_printer_2', 'caja_id', 'printer_name'
}
agregadas = 0
for k, v in nuevo.items():
    if k not in cliente:
        cliente[k] = v
        agregadas += 1
    elif k in claves_protegidas:
        pass  # No pisar datos del cliente

# Asegurar que db_path este limpio
cliente['db_path'] = ''

with open(cfg_cliente, 'w', encoding='utf-8') as f:
    json.dump(cliente, f, indent=4, ensure_ascii=False)

print(f'[OK] Configuracion actualizada ({agregadas} claves nuevas agregadas)')
" 2>nul

:: Limpiar pycache viejo
echo  Limpiando cache...
for /d /r "%DESTINO%" %%d in (__pycache__) do (
    if exist "%%d" rd /s /q "%%d" 2>nul
)
echo  [OK] Cache limpiado

echo.
echo  ========================================
echo   ACTUALIZACION COMPLETADA!
echo   Abre el programa normalmente.
echo  ========================================
echo.
pause
