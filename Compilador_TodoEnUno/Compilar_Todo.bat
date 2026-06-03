@echo off
title COMPILADOR MAESTRO - TPV PRO
color 0A

echo =====================================================================
echo                COMPILADOR MAESTRO - TODO EN UNO
echo =====================================================================
echo Este script automatiza los 3 pasos clave para publicar tu sistema:
echo 1) Compilar el codigo fuente (main.py) a un programa real (.exe)
echo 2) Comprimir y proteger los binarios en un .zip para Firebase
echo 3) Compilar el Instalador Web liviano que enviaras a tus clientes
echo =====================================================================
echo.
pause

echo.
echo =====================================================================
echo PASO 1: COMPILANDO EL SISTEMA BASE (ESTO TARDARA UNOS MINUTOS...)
echo =====================================================================
:: Nota de aprendizaje: Usamos 'python -m PyInstaller' para asegurarnos de que
:: use la instalacion global de Python y no falle.
:: La bandera --onedir crea una carpeta en lugar de un solo archivo, lo cual
:: hace que el programa abra mas rapido.

if exist "..\build" rd /s /q "..\build"
if exist "..\dist\CobroFacil_POS" rd /s /q "..\dist\CobroFacil_POS"

cd ..
python -m PyInstaller --noconfirm --onedir --windowed --name "CobroFacil_POS" ^
  --hidden-import "reportlab.graphics.barcode.code93" ^
  --hidden-import "reportlab.graphics.barcode.code128" ^
  --hidden-import "reportlab.graphics.barcode.code39" ^
  --hidden-import "reportlab.graphics.barcode.eanbc" ^
  --hidden-import "lxml" ^
  --hidden-import "html5lib" ^
  --hidden-import "openpyxl" ^
  --add-data "src/styles.qss;src/" ^
  main.py

echo.
echo =====================================================================
echo PASO 2: EMPAQUETANDO EL ZIP PARA FIREBASE
echo =====================================================================
:: Nota de aprendizaje: Aqui llamamos a tu script en Python que toma
:: la carpeta 'dist\CobroFacil_POS' recien creada y la comprime en
:: un archivo .zip blindado para que lo subas a la nube.

python empaquetar_para_firebase.py


echo.
echo =====================================================================
echo PASO 3: COMPILANDO EL INSTALADOR WEB (EL QUE ENVIAS AL CLIENTE)
echo =====================================================================
:: Nota de aprendizaje: Ahora entramos a la carpeta del instalador web
:: y usamos PyInstaller con la bandera --onefile para crear un unico .exe.
:: Este .exe descargara el ZIP de Firebase al ejecutarse.

cd launcher_installer
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

python -m PyInstaller --noconfirm --onefile --windowed ^
  --name "Setup_CobroFacil_Web" ^
  --hidden-import "win32com" ^
  --hidden-import "win32com.client" ^
  --icon=NONE ^
  --add-data "web;web" ^
  Instalador_Web.py

echo.
echo =====================================================================
echo PASO 4: MOVIENDO EL INSTALADOR A ESTA CARPETA
echo =====================================================================
:: Copiamos el .exe final a esta misma carpeta para tu comodidad
copy "dist\Setup_CobroFacil_Web.exe" "..\Compilador_TodoEnUno\" /Y

echo.
echo =====================================================================
echo                       ¡PROCESO TERMINADO!
echo =====================================================================
echo Que logramos hoy:
echo - El proyecto pesado fue compilado y empaquetado en un archivo .zip
echo   listo para que lo subas a Firebase Storage.
echo - El Instalador Web fue compilado y movido a esta misma carpeta:
echo   Compilador_TodoEnUno\Setup_CobroFacil_Web.exe
echo =====================================================================
echo Ya puedes enviarle Setup_CobroFacil_Web.exe a tus clientes.
pause
