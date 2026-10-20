# Plano - Motor de Backup y Compresión

## Frente

El administrador accede desde Configuración -> Mantenimiento -> Respaldo.
- **Exportar**: Permite guardar una copia (ZIP o SQL) manualmente.
- **Restaurar**: Abre el dialogo_restaurar.py para elegir una copia interna o de una ruta externa.

## Fondo

El sistema utiliza el CerebroBackup (`ritmo/motor_backup.py`) que corre en un hilo secundario (daemon) durante todo el día. El volcado lo hace `src/base_de_datos/autoblindaje/`.

1. **Ciclo de 30 minutos:** `ritmo/motor_backup.py` `_tick`. Cada 30 minutos guarda la base entera. El `backup_diario` del día es todo, más lo del día. La media hora (`backup_periodico`) es ese mismo todo, con el último ticket adentro. Si el ticket no está en el volcado, no se pisa la copia anterior. Si esta PC es la maestra, el volcado sale de su MariaDB local. Si es esclava, `host_vivo` pregunta en la red quién es la maestra ahora (`PUNPRO_DISCOVER`, UDP 37020). No usa una IP guardada. Un fallo no se anota como copia hecha.
2. **Cierre Diario:** `cierre/compresor.py` `comprimir_backups_del_dia`. Al cierre Z comprime los archivos del día en cada carpeta. El `backup_diario` del día no se borra. Si el zip no se puede leer, no se borra nada.
3. **Restauración:** `src/base_de_datos/restaurar/` lee los zip y las copias de 30 minutos. La cura automática está en `autoblindaje/sanar/`.

## Qué no cambiar

- El motor debe correr en un QThread o hilo demonio para no congelar la interfaz.
- La compresión no debe interrumpir ni bloquear la escritura en la base de datos principal.
