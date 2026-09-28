# Plano - Motor de Backup y Compresión

## Frente

El administrador accede desde Configuración -> Mantenimiento -> Respaldo.
- **Exportar**: Permite guardar una copia (ZIP o SQL) manualmente.
- **Restaurar**: Abre el dialogo_restaurar.py para elegir una copia interna o de una ruta externa.

## Fondo

El sistema utiliza el CerebroBackup (motor_backup.py) que corre en un hilo secundario (daemon) durante todo el día.

1. **Ciclo de 30 minutos:** Cada 30 minutos, el sistema guarda una copia de la base de datos localmente (en la carpeta segura de AppData/instalación) y, simultáneamente, en una **Ruta Externa** configurada. Esta doble vía previene pérdidas si una actualización borra la carpeta principal.
2. **Cierre Diario (00:00 hs):** Cuando se ejecuta el cierre Z o se hace el mantenimiento de medianoche, el sistema agrupa los backups generados cada 30 minutos en ese día, los **comprime en un único archivo .zip**, y elimina los archivos sueltos para ahorrar espacio.
3. **Restauración Autónoma:** El sistema lee tanto los zips diarios como las copias de 30 minutos al abrir el diálogo de restauración, permitiendo retroceder a puntos exactos.

## Qué no cambiar

- El motor debe correr en un QThread o hilo demonio para no congelar la interfaz.
- La compresión no debe interrumpir ni bloquear la escritura en la base de datos principal.
