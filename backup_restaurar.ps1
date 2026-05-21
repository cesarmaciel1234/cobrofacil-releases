# ╔══════════════════════════════════════════════════════════════╗
# ║        TPV PRO 2026 - SISTEMA DE BACKUP Y RESTAURACIÓN       ║
# ╚══════════════════════════════════════════════════════════════╝

param(
    [string]$Modo = "backup",   # "backup" o "restaurar"
    [string]$ArchivoZip = ""    # Solo para restaurar: ruta al .zip
)

$PROYECTO = "c:\Users\cesar\OneDrive\Desktop\tpv pro 2026"
$BACKUPS  = "c:\Users\cesar\OneDrive\Desktop\BACKUPS_TPV"

# Asegurarse que la carpeta de backups existe
New-Item -ItemType Directory -Force -Path $BACKUPS | Out-Null

# ─── MODO BACKUP ───────────────────────────────────────────────
if ($Modo -eq "backup") {
    $fecha  = Get-Date -Format "yyyyMMdd_HHmm"
    $zip    = "$BACKUPS\TPV_Pro_2026_$fecha.zip"
    $temp   = "$env:TEMP\tpv_bk_$fecha"

    Write-Host ""
    Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  TPV PRO 2026  ·  CREANDO BACKUP         " -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Fecha   : $fecha"
    Write-Host "  Destino : $zip"
    Write-Host ""

    # Copiar el proyecto excluyendo archivos innecesarios
    Write-Host "  [1/4] Copiando archivos del proyecto..." -ForegroundColor Yellow
    Copy-Item -Path $PROYECTO -Destination $temp -Recurse -Force

    Write-Host "  [2/4] Limpiando archivos temporales..."  -ForegroundColor Yellow
    Get-ChildItem $temp -Recurse -Include "*.pyc"               | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem $temp -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem $temp -Recurse -Directory -Filter ".venv"       | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem $temp -Recurse -Directory -Filter ".git"        | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem $temp -Recurse -Directory -Filter "BACKUPS_TPV" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "  [3/4] Comprimiendo en ZIP..."            -ForegroundColor Yellow
    Compress-Archive -Path "$temp\*" -DestinationPath $zip -Force

    # Limpiar carpeta temporal
    Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue

    $size = [math]::Round((Get-Item $zip).Length / 1MB, 2)

    Write-Host "  [4/4] Backup completado."                -ForegroundColor Green
    Write-Host ""
    Write-Host "  ✅  BACKUP EXITOSO" -ForegroundColor Green
    Write-Host "      Archivo : $(Split-Path $zip -Leaf)"
    Write-Host "      Tamaño  : $size MB"
    Write-Host ""

    # Listar los últimos 5 backups disponibles
    Write-Host "  📦 Backups disponibles en $BACKUPS :" -ForegroundColor Cyan
    Get-ChildItem $BACKUPS -Filter "*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
        $sz = [math]::Round($_.Length / 1MB, 2)
        Write-Host "      $($_.Name)  ($sz MB)"
    }
    Write-Host ""
}

# ─── MODO RESTAURAR ────────────────────────────────────────────
elseif ($Modo -eq "restaurar") {

    Write-Host ""
    Write-Host "══════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host "  TPV PRO 2026  ·  RESTAURAR BACKUP       " -ForegroundColor Magenta
    Write-Host "══════════════════════════════════════════" -ForegroundColor Magenta

    # Si no se especificó archivo, mostrar los disponibles y pedir elección
    if (-not $ArchivoZip) {
        $backups = Get-ChildItem $BACKUPS -Filter "*.zip" | Sort-Object LastWriteTime -Descending
        if ($backups.Count -eq 0) {
            Write-Host "  ❌ No hay backups disponibles en $BACKUPS" -ForegroundColor Red
            exit 1
        }
        Write-Host "  Backups disponibles:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $backups.Count; $i++) {
            $sz = [math]::Round($backups[$i].Length / 1MB, 2)
            Write-Host "  [$i] $($backups[$i].Name)  ($sz MB)"
        }
        $sel = Read-Host "`n  Ingresa el número del backup a restaurar"
        $ArchivoZip = $backups[[int]$sel].FullName
    }

    if (-not (Test-Path $ArchivoZip)) {
        Write-Host "  ❌ Archivo no encontrado: $ArchivoZip" -ForegroundColor Red
        exit 1
    }

    Write-Host "  Restaurando: $(Split-Path $ArchivoZip -Leaf)"
    Write-Host ""
    $confirm = Read-Host "  ⚠️  ATENCIÓN: Esto reemplazará el proyecto actual. ¿Continuar? (S/N)"
    if ($confirm -notmatch "^[sS]$") {
        Write-Host "  Restauración cancelada." -ForegroundColor Yellow
        exit 0
    }

    # Crear un mini-backup de seguridad antes de restaurar
    $fechaActual = Get-Date -Format "yyyyMMdd_HHmm"
    $zipSeguridad = "$BACKUPS\ANTES_RESTAURAR_$fechaActual.zip"
    Write-Host "  [1/4] Guardando estado actual como seguridad..." -ForegroundColor Yellow
    Compress-Archive -Path "$PROYECTO\src" -DestinationPath $zipSeguridad -Force -ErrorAction SilentlyContinue

    # Extraer el backup seleccionado
    Write-Host "  [2/4] Extrayendo backup..."                      -ForegroundColor Yellow
    $tempRestore = "$env:TEMP\tpv_restore_$fechaActual"
    Expand-Archive -Path $ArchivoZip -DestinationPath $tempRestore -Force

    Write-Host "  [3/4] Restaurando archivos del proyecto..."      -ForegroundColor Yellow
    # Solo restauramos carpetas de código, no la BD ni la venv
    $carpetas = @("src", "main.py", "requirements.txt", "backup_restaurar.ps1")
    foreach ($item in $carpetas) {
        $origen_r = "$tempRestore\$item"
        if (Test-Path $origen_r) {
            Copy-Item -Path $origen_r -Destination $PROYECTO -Recurse -Force
        }
    }
    Remove-Item $tempRestore -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "  [4/4] Restauración completada."                  -ForegroundColor Green
    Write-Host ""
    Write-Host "  ✅  RESTAURACIÓN EXITOSA" -ForegroundColor Green
    Write-Host "      Backup de seguridad pre-restauración:"
    Write-Host "      $(Split-Path $zipSeguridad -Leaf)"
    Write-Host ""
}
else {
    Write-Host "  Uso:"
    Write-Host "  .\backup_restaurar.ps1 -Modo backup"
    Write-Host "  .\backup_restaurar.ps1 -Modo restaurar"
    Write-Host "  .\backup_restaurar.ps1 -Modo restaurar -ArchivoZip 'C:\...\backup.zip'"
}
