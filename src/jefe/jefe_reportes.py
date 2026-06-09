"""
jefe_reportes.py — Reportes y Ventas para el perfil JEFE
Reutiliza Admin3Reportes con señal de retorno al dashboard del Jefe.
"""
from src.admin.admin3_reportes import Admin3Reportes

# Re-exportar directamente — Admin3Reportes ya tiene request_dashboard signal
JefeReportes = Admin3Reportes
