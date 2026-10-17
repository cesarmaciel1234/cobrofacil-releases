# Motores del kiosk

Qué hace: timers de sync, sello TV, clima y watchdog de Chrome.

Qué función: `MotoresMixin._iniciar_motores` / `_on_sync_finished`.

Cómo funciona: `DbSyncWorker` llama `pulso_vitrina`. Si el pulso viene sin precios, no borra `rows_precios` y reintenta. El watchdog cada 3 s no abre otra Chrome si el perfil kiosk está ocupado o si hace menos de 15 s que se lanzó (el Popen de Windows se muere y deja la ventana).

Qué no debe cambiar: un sync `error` no deja la TV en negro.
