# cierre — el zip del día

`compresor.py`, función `comprimir_backups_del_dia(fecha_str)`.

## Qué hace

Al cierre Z o al mantenimiento de la noche junta los `.sql` y `.db` de esa fecha en `backup_consolidado_FECHA.zip`. El `backup_diario_FECHA.sql` se copia adentro y **queda suelto**: es el que se restaura. Si el zip no pasa la prueba, no se borra nada.

## Cómo corre

Recorre `AutoBlindajeDB.get_backup_directories()` (programa, AppData y Documentos). En cada una busca `*_{fecha}*.sql` y `*_{fecha}*.db`. No mete zip dentro de zip. Si el zip se lee bien, borra periódicos, turnos y el incremental `_ventas`. El `backup_diario` del día no se borra. Si el zip falla o no se puede leer, no se borra nada.

Lo llama `src/cerebro_global/cierre_caja_cerebro/procesos/cierre.py` cuando el tipo es `CIERRE_Z` o `CIERRE_DIARIO`.

## Qué no debe cambiar

- No comprimir una sola carpeta: las tres tienen que entrar en el mismo pase.
- No borrar el `backup_diario` del día.
- No borrar sueltos si el zip falló o no se puede leer.
