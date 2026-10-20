# sanar — revisar y volver atrás

`integridad.py`, clase `Sanar`. Corre al arrancar y cuando el restaurar pide una foto antes de pisar la base.

## Arranque

`verificar_y_respaldar_diario(engine, host)`:

1. En MariaDB, `host_vivo`. Si viene vacío, `replicar_espejo` y sale. No repara ni recrea tablas a ciegas.
2. Si el host no es esta PC, solo copia el `.sql` y sale. Una esclava no repara, no restaura y no borra tablas de la maestra.
3. `verificar_integridad`. SQLite: `PRAGMA quick_check`. MariaDB: `CHECK TABLE`. Una nota del motor («doesn't support check») no es corrupción. Solo un `Msg_type` error dispara la cura. Si no conecta, sigue como sana para no restaurar por un corte de red.
4. Si está mal, `auto_reparar_o_restaurar`. Si eso no alcanza, `restaurar_ultimo_backup_valido` con las ventas de hoy reinyectadas. Si tampoco hay copia usable, `_recrear_tablas_criticas_mariadb` deja tablas vacías, y solo si el host es esta PC. Eso se anota como pérdida, no como respaldo.
5. Después pide el diario del día (`force=False`), replica, limpia viejos y, si hay pendrive, copia ahí.

## Restaurar

- `crear_snapshot_pre_restore`: guarda `pre_restore_FECHA.sql` antes de pisar. Si el volcado falla y el host es esta PC, deja el zip físico. Si no, `None` y el restaurar sigue con aviso.
- `_exportar_delta_hoy` / `_reinyectar_delta_hoy`: ventas, detalle y movimientos de hoy. Sirven para restaurar un día anterior sin perder lo cobrado hoy. Si no se puede leer el delta, el log lo dice y no inventa filas.
- `restaurar_ultimo_backup_valido`: elige con `_list_usable_backups`. Salta los que `_is_quarantined` marcó. `only_today` no baja a un día viejo.
- `_aplicar_archivo_restore`: un `.zip` físico solo se descomprime en el MariaDB de esta PC. Un `.sql` va al host que se pidió; si el host viene vacío, no se aplica. Un `.zip` o `.sql` no pisa el `punpro.db` de una caja SQLite.
- `restaurar_archivo_con_merge`: aplica y después reinyecta el delta de hoy.

## Qué no debe cambiar

- Sin maestra no se recrean tablas ni se restaura.
- No aplicar un paquete MariaDB sobre el SQLite de emergencia.
- No restaurar un día anterior sin intentar el delta de hoy.
