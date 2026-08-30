@echo off
title COMPILADOR MAESTRO - TPV PRO
color 0A

echo =====================================================================
echo                COMPILADOR MAESTRO - TODO EN UNO
echo =====================================================================
echo Este script automatiza los pasos locales de empaquetado:
echo 1) Compilar el codigo fuente (main.py) a CobroFacil_POS.exe
echo 2) Empaquetar ZIP de release (mismo criterio que GitHub Actions)
echo 3) Compilar el Instalador Web liviano
echo =====================================================================
echo.
pause

echo.
echo =====================================================================
echo PASO 0: VERIFICANDO ICONOS DEL CLIMA
echo =====================================================================
python src\carteleria\lanzador_tv\generar_iconos_clima.py
if not exist "build" mkdir build
python -c "from src.carteleria.lanzador_tv.tv_cara_pack import pack_source; pack_source('build/tv_cara.bin')"

echo.
echo =====================================================================
echo PASO 1: COMPILANDO EL SISTEMA BASE (ESTO TARDARA UNOS MINUTOS...)
echo =====================================================================

if exist "..\build" rd /s /q "..\build"
if exist "..\dist\CobroFacil_POS" rd /s /q "..\dist\CobroFacil_POS"

cd ..
python -m PyInstaller --noconfirm --onedir --windowed --name "CobroFacil_POS" ^
  --exclude-module "rembg" ^
  --exclude-module "scipy" ^
  --exclude-module "src.carteleria.creador_png.convertir_imagen" ^
  --hidden-import "reportlab.graphics.barcode.code93" ^
  --hidden-import "reportlab.graphics.barcode.code128" ^
  --hidden-import "reportlab.graphics.barcode.code39" ^
  --hidden-import "reportlab.graphics.barcode.eanbc" ^
  --hidden-import "lxml" ^
  --hidden-import "html5lib" ^
  --hidden-import "openpyxl" ^
  --hidden-import "win32com" ^
  --hidden-import "win32com.client" ^
  --hidden-import "PyQt6.QtWebEngineWidgets" ^
  --hidden-import "PyQt6.QtWebEngineCore" ^
  --collect-all "PyQt6.QtWebEngineCore" ^
  --collect-all "PyQt6.QtWebEngineWidgets" ^
  --runtime-hook "01_Compiladores_y_Ejecutables/rthooks/pyi_rth_qt_dll_path.py" ^
  --collect-submodules "src.admin" ^
  --collect-submodules "src.jefe" ^
  --collect-submodules "src.carteleria" ^
  --collect-submodules "src.motor_descuentos" ^
  --collect-submodules "src.services" ^
  --hidden-import "src.carteleria.creador_png.app" ^
  --hidden-import "src.carteleria.creador_png.servidor" ^
  --hidden-import "flask" ^
  --hidden-import "jinja2" ^
  --hidden-import "werkzeug" ^
  --add-data "src/ui_components;src/ui_components" ^
  --add-data "src/assets;src/assets" ^
  --add-data "src/carteleria/assets;src/carteleria/assets" ^
  --add-data "build/tv_cara.bin;tv_cara.bin" ^
  --add-data "src/carteleria/creador_png/templates;src/carteleria/creador_png/templates" ^
  --add-data "src/carteleria/creador_png/static;src/carteleria/creador_png/static" ^
  --add-data "Catalogos;Catalogos" ^
  main.py

echo.
echo Compilando worker Creador PNG (recorte IA)...
python -m PyInstaller --noconfirm --onedir --console --name "Creador_PNG_Worker" ^
  --hidden-import "rembg" ^
  --collect-all "rembg" ^
  --collect-all "onnxruntime" ^
  --collect-all "pooch" ^
  src\carteleria\creador_png\convertir_imagen.py
if exist "dist\CobroFacil_POS\worker" rd /s /q "dist\CobroFacil_POS\worker"
if exist "dist\Creador_PNG_Worker" move "dist\Creador_PNG_Worker" "dist\CobroFacil_POS\worker"
python -c "from src.carteleria.lanzador_tv.tv_cara_pack import instalar_blob_en_dist; instalar_blob_en_dist(r'dist\CobroFacil_POS')"

echo.
echo =====================================================================
echo PASO 2: EMPAQUETANDO ZIP DE RELEASE
echo =====================================================================
python prepare_mariadb_release.py
python package_release_zip.py

echo.
echo =====================================================================
echo PASO 3: COMPILANDO EL INSTALADOR WEB (EL QUE ENVIAS AL CLIENTE)
echo =====================================================================

cd launcher_installer
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

python -m PyInstaller --noconfirm --onefile --windowed ^
  --name "Setup_CobroFacil_Web" ^
  --hidden-import "win32com" ^
  --hidden-import "win32com.client" ^
  --hidden-import "PyQt6.QtWebEngineWidgets" ^
  --hidden-import "PyQt6.QtWebEngineCore" ^
  --collect-all "PyQt6.QtWebEngineCore" ^
  --collect-all "PyQt6.QtWebEngineWidgets" ^
  --icon=NONE ^
  --add-data "web;web" ^
  Instalador_Web.py

echo.
echo =====================================================================
echo PASO 4: MOVIENDO EL INSTALADOR A ESTA CARPETA
echo =====================================================================
copy "dist\Setup_CobroFacil_Web.exe" "..\Compilador_TodoEnUno\" /Y

echo.
echo =====================================================================
echo                       PROCESO TERMINADO
echo =====================================================================
echo - dist\CobroFacil_POS_Release.zip listo (GitHub Releases)
echo - Compilador_TodoEnUno\Setup_CobroFacil_Web.exe
echo =====================================================================
pause
