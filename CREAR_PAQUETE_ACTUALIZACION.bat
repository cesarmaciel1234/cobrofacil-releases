@echo off
:: ============================================================
::  CREAR PAQUETE DE ACTUALIZACION - CAJAFACIL PRO
::  Ejecutar en TU PC cuando quieras lanzar una nueva version
::  Genera un .zip listo para compartir con los clientes
:: ============================================================
title Crear Paquete Cobro Fácil POS
color 0B
echo.
echo  ========================================
echo   CAJAFACIL PRO - CREAR PAQUETE UPDATE
echo  ========================================
echo.

cd /d "%~dp0"

:: Leer version del version.json
for /f "tokens=2 delims=:, " %%v in ('findstr "app_version" version.json') do (
    set VERSION=%%~v
    goto :got_version
)
:got_version
set VERSION=%VERSION:"=%
echo  Version detectada: %VERSION%

:: Actualizar checksums antes de empaquetar
echo.
echo  Actualizando checksums...
.venv\Scripts\python.exe generar_version.py
if errorlevel 1 (
    echo  ERROR actualizando version.json
    pause
    exit /b 1
)

:: Limpiar pycache antes de empaquetar
echo  Limpiando cache...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rd /s /q "%%d" 2>nul
)

:: Nombre del paquete
set PAQUETE=CobroFacil_POS_v%VERSION%.zip

:: Crear ZIP con PowerShell (sin programas externos)
echo.
echo  Creando %PAQUETE%...
if exist "%PAQUETE%" del "%PAQUETE%"

powershell -Command "
$excluir = @('.venv', '__pycache__', 'build', 'dist', 'backups', 'scratch', '.git', 'reportes', 'logs', 'data', 'Etiquetas_Impresas', 'Folletos_Oferta', 'Carteles_Oferta')
$base = Get-Location
$archivos = Get-ChildItem -Recurse -File | Where-Object {
    $path = $_.FullName
    $excluido = $false
    foreach ($ex in $excluir) {
        if ($path -like '*\' + $ex + '\*' -or $path -like '*\' + $ex) {
            $excluido = $true; break
        }
    }
    -not $excluido -and
    $_.Extension -notin @('.db', '.log', '.pyc', '.zip', '.exe') -and
    $_.Name -ne 'punpro.db'
}
$archivos | ForEach-Object { Write-Host '  +' $_.FullName.Replace($base.Path + '\', '') }
Compress-Archive -Path ($archivos.FullName) -DestinationPath '$env:PAQUETE' -Force
" 2>nul

:: Metodo alternativo mas simple
powershell -Command "
Add-Type -Assembly 'System.IO.Compression.FileSystem'
$base = (Get-Location).Path
$zip = [System.IO.Compression.ZipFile]::Open('%PAQUETE%', 'Create')
$excluir = @('.venv','__pycache__','build','dist','backups','scratch','.git','reportes','logs','data')
$exclExt = @('.db','.log','.pyc','.zip','.exe')
Get-ChildItem -Recurse -File | Where-Object {
    $rel = $_.FullName.Replace($base + '\', '')
    $partes = $rel.Split('\')
    $ok = $true
    foreach ($p in $partes) { if ($excluir -contains $p) { $ok = $false; break } }
    $ok -and ($exclExt -notcontains $_.Extension)
} | ForEach-Object {
    $rel = $_.FullName.Replace($base + '\', '')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $rel) | Out-Null
}
$zip.Dispose()
Write-Host 'ZIP creado exitosamente'
"

echo.
echo  ========================================
if exist "%PAQUETE%" (
    echo   PAQUETE LISTO: %PAQUETE%
    echo.
    echo   PROXIMOS PASOS:
    echo   1. Subir %PAQUETE% a Google Drive / Dropbox
    echo   2. Compartir el link de descarga con los clientes
    echo   3. Clientes ejecutan ACTUALIZAR.bat dentro del zip
    echo  ========================================
    :: Abrir carpeta para facil acceso
    explorer /select,"%~dp0%PAQUETE%"
) else (
    echo   ERROR: No se pudo crear el paquete
    echo  ========================================
)
echo.
pause
