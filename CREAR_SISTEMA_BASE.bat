@echo off
title Compilar Sistema Base - Cobro Facil POS
color 0B
echo ========================================================
echo   CAJAFACIL PRO - COMPILAR SISTEMA BASE (EJECUTABLE)
echo ========================================================
echo.
echo Preparando entorno y borrando compilaciones previas...
if exist "build" rd /s /q "build"
if exist "dist\CobroFacil_POS" rd /s /q "dist\CobroFacil_POS"

echo.
echo Ensamblando el ejecutable principal...
.\.venv\Scripts\pyinstaller.exe --noconfirm --onedir --windowed --name "CobroFacil_POS" ^
  --hidden-import "reportlab.graphics.barcode.code93" ^
  --hidden-import "reportlab.graphics.barcode.code128" ^
  --hidden-import "reportlab.graphics.barcode.code39" ^
  --hidden-import "reportlab.graphics.barcode.eanbc" ^
  --hidden-import "lxml" ^
  --hidden-import "html5lib" ^
  --hidden-import "openpyxl" ^
  --hidden-import "reportlab.graphics.barcode.qr" ^
  --hidden-import "reportlab.graphics.barcode.dmtx" ^
  --hidden-import "reportlab.graphics.barcode.ecc200datamatrix" ^
  --hidden-import "reportlab.graphics.barcode.fourstate" ^
  --hidden-import "reportlab.graphics.barcode.lto" ^
  --hidden-import "reportlab.graphics.barcode.qrencoder" ^
  --hidden-import "reportlab.graphics.barcode.usps" ^
  --hidden-import "reportlab.graphics.barcode.usps4s" ^
  --hidden-import "reportlab.graphics.barcode.widgets" ^
  --hidden-import "reportlab.graphics.barcode.common" ^
  --add-data "src/styles.qss;src/" ^
  main.py

echo ========================================================
echo   COMPILACION FINALIZADA.
echo   El sistema base esta en la carpeta "dist\CobroFacil_POS"
echo ========================================================
pause
