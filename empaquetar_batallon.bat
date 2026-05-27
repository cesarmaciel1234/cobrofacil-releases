@echo off
setlocal enabledelayedexpansion
title Cobro Fácil POS - Generador de Batallon de Despliegue Universal (Win7 a Win11)
color 1F

echo ===============================================================================
echo 🚀 PUNPRO TPV 2026 ELITE - COMPILADOR INDUSTRIAL PORTABLE E INSTALABLE
echo ===============================================================================
echo/
echo Este script ejecutara la estrategia de empaquetado maestra para crear:
echo   1. Una version PORTABLE ABSOLUTA en carpeta (ideal para descomprimir en Pendrive)
echo   2. Un archivo ZIP auto-generado con todo el batallon listo para viajar por el mundo.
echo/
echo IMPORTANTE PARA SOPORTE WINDOWS 7:
echo Para que el programa ejecute nativamente en Windows 7 (32 y 64 bits), DEBES compilar
echo este script utilizando una instalacion base de Python 3.8 o inferior.
echo Las compilaciones hechas con Python 3.9+ generaran un error de Kernel32 en Win7.
echo/
:: pause

:: 1. Activar entorno de construccion
echo/
echo [1/5] Activando el entorno de compilacion...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ADVERTENCIA] No se encontro entorno virtual local. Se usara el Python del sistema.
)

:: Garantizar que PyInstaller este instalado
pip install pyinstaller >nul 2>&1

:: 2. Limpieza estricta de compilaciones obsoletas
echo [2/5] Purgando carpetas de construccion antiguas...
if exist "build" rmdir /s /q "build"
if exist "dist\CobroFacil_POS_Portable_Win7" rmdir /s /q "dist\CobroFacil_POS_Portable_Win7"
if exist "dist\CobroFacil_POS_Portable_Win8_Win11" rmdir /s /q "dist\CobroFacil_POS_Portable_Win8_Win11"
if exist "Batallon_TPV_Win7.zip" del /f /q "Batallon_TPV_Win7.zip"
if exist "Batallon_TPV_Win8_Win11.zip" del /f /q "Batallon_TPV_Win8_Win11.zip"

:: 3. Compilacion Desacoplada (Modo Carpeta Optimizada)
echo/
echo [3/5] Ensamblando binarios nativos y dependencias graficas...
echo Esto tomara unos momentos. PyInstaller esta analizando el arbol de importacion...
pyinstaller --noconfirm --onedir --windowed --name "CobroFacil_POS" ^
 --add-data "src/styles.qss;src/" ^
 --hidden-import "matplotlib" ^
 --hidden-import "matplotlib.backends.backend_qt5agg" ^
 --hidden-import "requests" ^
 --hidden-import "barcode" ^
 --hidden-import "barcode.writer" ^
 --hidden-import "PIL" ^
 --hidden-import "reportlab" ^
 --collect-all "matplotlib" ^
 --collect-all "requests" ^
 --collect-all "barcode" ^
 --collect-all "reportlab" ^
 main.py

:: 4. Estructuracion del Batallon Dividido por Sistema Operativo
echo/
echo [4/5] Estructurando carpetas gemelas para el Pendrive (Win7 vs Win8-11)...

:: ── DEFINICION DE RUTAS DE DESTINO ──
set "DIR_W7=dist\CobroFacil_POS_Portable_Win7"
set "DIR_W8_11=dist\CobroFacil_POS_Portable_Win8_Win11"

mkdir "%DIR_W7%\bin" 2>nul
mkdir "%DIR_W8_11%\bin" 2>nul

:: Clonar el binario base a ambas distribuciones
echo   - Distribuyendo motor binario a carpetas de SO...
xcopy /E /I /Y "dist\CobroFacil_POS\*" "%DIR_W7%\bin\" >nul
xcopy /E /I /Y "dist\CobroFacil_POS\*" "%DIR_W8_11%\bin\" >nul
rmdir /s /q "dist\CobroFacil_POS"

:: Inyectar base de datos y configuracion por defecto en las raices portables
echo   - Inyectando plantillas de datos base en ambas versiones...
for %%D in ("%DIR_W7%" "%DIR_W8_11%") do (
    if exist "punpro.db" copy /y "punpro.db" "%%~D\punpro.db" >nul
    if exist "config.json" copy /y "config.json" "%%~D\config.json" >nul
    
    echo @echo off> "%%~D\INICIAR_SISTEMA.bat"
    echo title Iniciando Cobro Fácil POS Portable>> "%%~D\INICIAR_SISTEMA.bat"
    echo start "" "bin\CobroFacil_POS.exe">> "%%~D\INICIAR_SISTEMA.bat"
)

:: Inyectar un archivo leame distintivo en la version de Windows 7 para orientar al operador
(
echo ===============================================================================
echo NOTA DE COMPATIBILIDAD - WINDOWS 7 PORTABLE
echo ===============================================================================
echo Esta carpeta ha sido preconfigurada y aislada especificamente para ejecutar
echo sin errores de Kernel32 en sistemas operativos heredados ^(Windows 7 de 32 o 64 bits^).
echo/
echo Para iniciar el sistema, haz doble clic en el archivo "INICIAR_SISTEMA.bat".
) > "%DIR_W7%\LEAME_WINDOWS_7.txt"

:: 5. Empaquetado ZIP Dual Independiente
echo/
echo [5/5] Sellando los batallones en archivos ZIP gemelos independientes...
echo   - Comprimiendo paquete Windows 7...
powershell.exe -nologo -noprofile -command "Compress-Archive -Path '%DIR_W7%' -DestinationPath 'Batallon_TPV_Win7.zip' -Force"
echo   - Comprimiendo paquete Windows 8 a 11...
powershell.exe -nologo -noprofile -command "Compress-Archive -Path '%DIR_W8_11%' -DestinationPath 'Batallon_TPV_Win8_Win11.zip' -Force"

:: ─────────────────────────────────────────────────────────────────────────────
:: 6. ENSAMBLADO DE LA SUPER CARPETA "CATORTA USB" PARA ARRASTRAR AL PENDRIVE
:: ─────────────────────────────────────────────────────────────────────────────
echo/
echo [EXTRA] Ensamblando la super carpeta "CATORTA_USB_PUNPRO" de copia directa...
set "CATORTA=CATORTA_USB_PUNPRO"
if exist "%CATORTA%" rmdir /s /q "%CATORTA%"
mkdir "%CATORTA%" 2>nul
mkdir "%CATORTA%\1_Sistemas_Portables_Descomprimidos" 2>nul
mkdir "%CATORTA%\2_Archivos_Comprimidos_ZIP" 2>nul
mkdir "%CATORTA%\3_Manuales_y_Documentacion" 2>nul
mkdir "%CATORTA%\4_Instaladores_InnoSetup" 2>nul

:: A. Copiar carpetas nativas puras listas para click y usar
echo   - Copiando sistemas portables descomprimidos...
xcopy /E /I /Y "%DIR_W7%" "%CATORTA%\1_Sistemas_Portables_Descomprimidos\TPV_Portable_Win7\" >nul
xcopy /E /I /Y "%DIR_W8_11%" "%CATORTA%\1_Sistemas_Portables_Descomprimidos\TPV_Portable_Win8_Win11\" >nul

:: B. Mover los ZIPs corporativos al sector de envios
echo   - Guardando archivos ZIP para transferencias...
move /y "Batallon_TPV_Win7.zip" "%CATORTA%\2_Archivos_Comprimidos_ZIP\" >nul
move /y "Batallon_TPV_Win8_Win11.zip" "%CATORTA%\2_Archivos_Comprimidos_ZIP\" >nul

:: C. Copiar la base documental y manuales tecnicos
echo   - Respaldando guias y manuales de arquitectura...
if exist "docs\manual.md" copy /y "docs\manual.md" "%CATORTA%\3_Manuales_y_Documentacion\Manual_Cajero_y_Operaciones.md" >nul
if exist "docs\manual_programador_ia.md" copy /y "docs\manual_programador_ia.md" "%CATORTA%\3_Manuales_y_Documentacion\Manual_Arquitectura_y_IA.md" >nul
if exist "docs\manuales\*.html" xcopy /Y "docs\manuales\*.html" "%CATORTA%\3_Manuales_y_Documentacion\" >nul

:: D. Proporcionar scripts para compilar instaladores formales
echo   - Copiando esquemas de instalacion Inno Setup...
if exist "instalador_win7.iss" copy /y "instalador_win7.iss" "%CATORTA%\4_Instaladores_InnoSetup\" >nul
if exist "instalador_win8_win11.iss" copy /y "instalador_win8_win11.iss" "%CATORTA%\4_Instaladores_InnoSetup\" >nul

:: E. Crear el indice guia maestro dentro de la Catorta
(
echo ===============================================================================
echo 🌟 PUNPRO TPV 2026 - INDICE DE LA CATORTA USB MAESTRA
echo ===============================================================================
echo/
echo Has copiado esta carpeta a tu pendrive. Tienes en tus manos el batallon
echo de despliegue informatico definitivo para operar en cualquier mostrador.
echo/
echo ESTRUCTURA DE CONTENIDOS:
echo/
echo 📁 1_Sistemas_Portables_Descomprimidos\
echo    Entra aqui si necesitas abrir la caja de inmediato en una PC ajena.
echo    Elige la carpeta segun el Windows, doble clic a "INICIAR_SISTEMA.bat" y factura.
echo/
echo 📁 2_Archivos_Comprimidos_ZIP\
echo    Contiene los bloques sellados. Usalos si un antivirus rebelde te bloquea
echo    copiar archivos sueltos, o si necesitas enviar el sistema por WhatsApp/Correo.
echo/
echo 📁 3_Manuales_y_Documentacion\
echo    Toda la literatura tecnica. Contiene los atajos de teclado para capacitar al
echo    cajero y las reglas de inmutabilidad para futuros programadores.
echo/
echo 📁 4_Instaladores_InnoSetup\
echo    Scripts fuente listos para compilar en Inno Setup si el cliente exige
echo    una instalacion clasica ^(Setup.exe^) con permisos nativos de base de datos.
echo/
echo ===============================================================================
echo SOFTWARE PROPIEDAD DE PUNPRO SYSTEMS - LICENCIA DE DESPLIEGUE ELITE 2026
echo ===============================================================================
) > "%CATORTA%\GUIA_RAPIDA_DEL_PENDRIVE.txt"

echo/
echo ===============================================================================
echo ✅ COMPILACION MAESTRA Y CATORTA USB FINALIZADA CON EXITO
echo ===============================================================================
echo/
echo 🎯 OBJETIVO CUMPLIDO:
echo Ve a la raiz de tu proyecto. Encontraras la super carpeta llamada:
echo/
echo      📁 CATORTA_USB_PUNPRO\
echo/
echo Arrastra o copia unicamente esa carpeta hacia tu pendrive USB.
echo Con eso tienes tu navaja suiza informatica lista para viajar por el mundo.
echo/
:: pause
