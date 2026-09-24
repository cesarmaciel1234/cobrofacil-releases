# Escucha en vivo

`mp_polling_thread.py`, clase `MPPollingThread`.

La arranca `EscuchaMP.asegurar()` en `src/services/mp_escucha.py`, con el token `mp_access_token` de la configuración. El monitor no abre otro hilo.

`run()` la primera vuelta marca los pagos ya aprobados y no avisa. Después emite `new_payment` si el cobro es de esta cuenta, está aprobado y tiene menos de 180 segundos. Un 401 emite `error_signal` y frena el hilo.

`stop()` corta el ciclo. No hay que frenarlo al salir del monitor: el cajero usa el mismo hilo.
