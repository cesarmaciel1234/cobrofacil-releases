@echo off
title Cerrando procesos de CobroFacil POS
echo Deteniendo procesos en ejecucion de CobroFacil_POS y MariaDB...
taskkill /f /im CobroFacil_POS.exe 2>nul
taskkill /f /im mysqld.exe 2>nul
echo.
echo Procesos finalizados con exito. Ya puedes extraer o reemplazar los archivos del programa.
pause
