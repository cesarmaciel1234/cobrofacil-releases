# ritmo — cada 30 minutos

`motor_backup.py`. La instancia es `cerebro_backup`.

## Qué hace

Pide el `.sql` del día sin frenar la pantalla. El volcado en sí está en `src/base_de_datos/autoblindaje/`.

## Cómo corre

`start(engine, host)` abre un hilo demonio. La primera pasada espera 45 segundos. Después, `INTERVAL_SEC` (30 minutos).

`_tick`:

1. `drenar_cola` sube cobros que quedaron en el diario local. Si falla, el tick sigue.
2. `AutoBlindajeDB.host_vivo`. Si es MariaDB y no hay maestra, guarda `last_mode` `sin_maestra`, `last_ok` false, y no escribe archivo.
3. Cuenta ventas nuevas solo para el log. No cambia el tipo de copia.
4. Siempre graba el diario completo: toda la base, con el día adentro. Si el último ticket no está en el volcado, no reemplaza el archivo.
5. Si eso salió bien, `sellar_media_hora` copia ese mismo archivo a `backup_periodico_AHORA`. Esa es la media hora: todo, más el último ticket.
6. `last_full_at` se mueve solo cuando `ok` es verdadero. El estado queda en `cerebro_backup_state.json`, dentro de AppData `backups\db`.

`tick_now(force_full)` es el mismo ciclo, al momento. Lo usa el cierre manual.

## Qué no debe cambiar

- No anotar éxito si `host_vivo` vino vacío o el volcado devolvió `False`.
- Si el volcado falla, reintenta dos veces más y olvida el host entre intentos.
- No correr el volcado en el hilo de la pantalla.
- El estado se reemplaza entero. Un corte no deja el sello a medias.
