@echo off
REM Arranque autonomo: si el EXE quedo corrupto tras un update, restaura el .old
REM antes de lanzar (el bootloader PyInstaller no puede auto-repararse solo).
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$exe='CobroFacil_POS.exe'; $old='CobroFacil_POS.exe.old'; " ^
  "function Ok($p){ if(-(Test-Path $p)){return $false}; $s=(Get-Item $p).Length; if($s -lt 50000){return $false}; " ^
  "$fs=[IO.File]::OpenRead($p); $b=New-Object byte[] 2; [void]$fs.Read($b,0,2); " ^
  "$fs.Seek([Math]::Max(0,$s-8192),'Begin')|Out-Null; $t=New-Object byte[] 8192; $n=$fs.Read($t,0,8192); $fs.Close(); " ^
  "$tail=[Text.Encoding]::ASCII.GetString($t,0,$n); return ($b[0]-eq 77 -and $b[1]-eq 90 -and $tail.Contains('MEI')) }; " ^
  "if((Test-Path $old) -and (-not (Ok $exe))){ Copy-Item -Force $old $exe; Write-Host 'EXE restaurado desde .old' }; " ^
  "if((Test-Path $old) -and (Test-Path $exe)){ " ^
  "  if( ((Get-Item $exe).Length + 40000) -lt (Get-Item $old).Length ){ Copy-Item -Force $old $exe; Write-Host 'EXE truncado: restaurado .old' } }"

if not exist "CobroFacil_POS.exe" (
  echo No se encuentra CobroFacil_POS.exe
  pause
  exit /b 1
)

start "" "CobroFacil_POS.exe" %*
endlocal
