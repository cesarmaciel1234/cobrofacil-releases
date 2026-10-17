# Motores del kiosk

Qué hace: timers de sync, sello TV, clima y watchdog de Chrome.

Qué función: `MotoresMixin._iniciar_motores` / `_on_sync_finished`.

Cómo funciona: `DbSyncWorker` llama `pulso_vitrina`. Si el pulso viene sin precios, no borra `rows_precios` y reintenta. Si Chrome se cerró, lo reabre en el mismo puerto.

Qué no debe cambiar: un sync `error` no deja la TV en negro.
