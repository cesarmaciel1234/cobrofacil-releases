# Configuración del sistema

Hub admin (General, Personalización, Dispositivos, etc.).

## Lectura en monitores chicos

Tipografía y tamaño de tiles se ajustan **acá**, en `componentes/config_button.py` y la barra de `configuracion_main.py`. No tocar `src/utils/qt_dpi.py`: eso escala toda la app.

## Respaldo (Mantenimiento)

- `componentes/dialogo_respaldo.py`: «Exportar / Crear Respaldo» hace `mysqldump --host=<maestra>` a un `.sql` (o copia `punpro.db` si la tienda es SQLite sola). Toma la tienda de `restaurar.destino_actual()`: una caja sin maestra no exporta su base de emergencia. «Importar / Restaurar Respaldo» abre el diálogo de abajo.
- `componentes/dialogo_restaurar.py`: elegir la copia y restaurar. Busca en un hilo (`_Busqueda`) y restaura en otro (`_Trabajo`), así la pantalla no se congela. Marca la copia más nueva; se puede tocar otra. Muestra los avisos de `revisar` (ámbar) o los bloqueos (rojo, sin botón). Pide la clave del jefe (`CLAVE_RED` o la de Super User) y confirma con los avisos. No se cierra mientras restaura.
- El motor es `src/base_de_datos/restaurar` (README). Sirve igual un respaldo o el pendrive del jefe. Para leer cualquier copia hace falta el sistema instalado: la tienda trabaja con MariaDB.
