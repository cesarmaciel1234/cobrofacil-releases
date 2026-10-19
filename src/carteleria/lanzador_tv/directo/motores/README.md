# Motores del kiosk

Qué hace: timers de sync, sello TV, clima y watchdog de Chrome.

Qué función: `MotoresMixin._iniciar_motores` / `_on_sync_finished`.

Cómo funciona: `DbSyncWorker` llama `pulso_vitrina` en un hilo cada 15 s. El sello (`carteleria_datos.sello`) se mira cada 1 s: un precio, una oferta o un aviso nuevo dispara el mismo pulso sin esperar. Ahí se arma el ranking de la maestra. El slot de la pantalla solo copia lo que ya llegó: no abre HTTP ni MariaDB. Si el pulso viene sin precios, no borra `rows_precios` y reintenta. El watchdog cada 3 s no abre otra Chrome si el perfil kiosk está ocupado o si hace menos de 15 s que se lanzó (el Popen de Windows se muere y deja la ventana). Si la cara no avisa `/api/viva` en 25 s, reabre esa misma ventana.

Qué no debe cambiar: un sync `error` no deja la TV en negro.
