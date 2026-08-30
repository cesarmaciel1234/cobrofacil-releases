@echo off
title Compilar Sistema Base - Cobro Facil POS
color 0B
echo ========================================================
echo   CAJAFACIL PRO - COMPILAR SISTEMA BASE (EJECUTABLE)
echo ========================================================
echo.
echo PASO 0: Verificando iconos del clima...
python src\carteleria\lanzador_tv\generar_iconos_clima.py
echo.
echo Preparando entorno y borrando compilaciones previas...
if exist "build" rd /s /q "build"
if exist "dist\CobroFacil_POS" rd /s /q "dist\CobroFacil_POS"
mkdir build
python -c "from src.carteleria.lanzador_tv.tv_cara_pack import pack_source; pack_source('build/tv_cara.bin')"

echo.
echo Ensamblando el ejecutable principal...
.\.venv\Scripts\pyinstaller.exe --noconfirm --onedir --windowed --name "CobroFacil_POS" ^
  --hidden-import "pymysql" ^
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
  --add-data "src/ui_components;src/ui_components" ^
  --add-data "src/assets;src/assets" ^
  --add-data "src/carteleria/assets;src/carteleria/assets" ^
  --add-data "build/tv_cara.bin;tv_cara.bin" ^
  --add-data "src/carteleria/creador_png/templates;src/carteleria/creador_png/templates" ^
  --add-data "src/carteleria/creador_png/static;src/carteleria/creador_png/static" ^
  --add-data "Catalogos;Catalogos" ^
  --collect-submodules "src.carteleria" ^
  --collect-submodules "src.motor_descuentos" ^
  --hidden-import "src.carteleria.creador_png.app" ^
  --hidden-import "flask" ^
  --hidden-import "jinja2" ^
  --hidden-import "werkzeug" ^
  --copy-metadata "werkzeug" ^
  --copy-metadata "flask" ^
  --copy-metadata "jinja2" ^
  --collect-all "flask" ^
  --collect-all "werkzeug" ^
  --runtime-hook "01_Compiladores_y_Ejecutables/rthooks/pyi_rth_pkg_metadata.py" ^
  main.py

python -c "from src.carteleria.lanzador_tv.tv_cara_pack import instalar_blob_en_dist; instalar_blob_en_dist(r'dist\CobroFacil_POS')"

echo ========================================================
echo   COMPILACION FINALIZADA.
echo   El sistema base esta en la carpeta "dist\CobroFacil_POS"
echo ========================================================
