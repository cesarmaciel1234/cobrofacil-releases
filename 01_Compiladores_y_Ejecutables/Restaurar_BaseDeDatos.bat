@echo off
title Asistente de Restauracion de Base de Datos - Cobro Facil
cd /d "%~dp0"
echo Iniciando Asistente...
if exist _internal\python.exe (
    _internal\python.exe restaurar_backup.py
) else (
    python restaurar_backup.py
)
