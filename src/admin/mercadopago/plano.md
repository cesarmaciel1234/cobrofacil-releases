# Plano — monitor de Mercado Pago

La rama arranca en esta carpeta. La base es `src/admin` y no lleva plano.

## Frente

`mercadopago_main.py`, clase `Admin10MP`. Se abre desde el menú de admin.

Arriba: volver, el título, el interruptor «Cajero silencioso» / «Con sonido», Actualizar y el estado. No hay campo de token, ni «Guardar e Iniciar», ni «Simular», ni importar un CSV a mano.

El cuerpo son las cinco tarjetas, el buscador, el filtro de fecha y la tabla. El clic derecho omite un pago o lo restaura.

## Fondo

El token es `mp_access_token` de la configuración del TPV. Lo lee `EscuchaMP.token()` en `src/services/mp_escucha.py`. Esta pantalla no lo guarda.

**Token de tienda (nuevo):** la maestra, al guardar Terminal TPV, publica el token en MariaDB `configuracion` (`sync_tienda/mp_token`). La esclava lo trae sola al conectar y al abrir el monitor. No hay que pegar el token en cada notebook. Si aún dice SIN TOKEN, en la PC de caja (maestra) hay que Guardar una vez el Terminal TPV para publicarlo.

**Fuera de red:** el nodo portable lleva también `reportes/mercado_pago_sync.csv` y `reportes/mp_vinculos.json`. Al abrir el monitor o pulsar **Actualizar**, la copia del nodo se combina antes de pintar. **Actualizar** luego baja el mes actual vía API y sincroniza por ID al nodo; cada pago que llega en vivo también queda copiado. Se combinan pagos nuevos, cambios de omitido/restaurado y tickets asociados. Si no hay token o la API no responde, el monitor muestra la copia local; si el nodo configurado está desconectado, informa que la sincronización quedó pendiente.

La columna **Ticket** prioriza el archivo local/nodo para conservar lo recién asociado y complementa los pagos con `mp_pagos.ticket` de la base compartida. De ese modo la asociación que subió otra PC de la LAN se ve en esta caja también. El monitor lee la asociación puramente del archivo JSON estático local (vinculo_mp) para evitar el bloqueo y saturación de consultas a la base de datos. Asociar en caja o sincronizar el nodo despierta el motor para que publique los vínculos sin esperar los 5 minutos del ciclo normal.

**Esclava:** ventas/stock = MariaDB. El historial MP (CSV) se baja con ese token vía API cuando hay conexión. `mp_vinculos.json` se mantiene local hasta sincronizar el nodo, que permite llevarlo y traerlo junto al historial.

`iniciar_monitor` llama `traer()` y después `EscuchaMP.asegurar()`. Es el mismo hilo que el cajero, `MPPollingThread` en `componentes/`. No se frena al salir del monitor.

`historial/sincronizar.py`, `bajar_mes`, baja los cobros aprobados del mes, de punta a punta. Actualizar y la apertura del monitor lo corren en `_BajadaMes`, fuera de la ventana: el estado pasa a ACTUALIZANDO y después vuelve a ESCUCHANDO. El botón pinta la grilla al toque, desde el archivo, aunque la bajada siga. Si la API no responde, queda visible la copia local con el estado SIN RED · COPIA LOCAL. La consulta lleva fecha de inicio y de fin; sin la de fin la API no devuelve pagos. La hora de la grilla es la de Argentina. Una transferencia recibida no se esconde con las cargas propias. Point y el QR llevan el mismo nombre que la app. `historial/archivo.py` los escribe en `reportes/mercado_pago_sync.csv` y `leer` arma las tarjetas. Un pago nuevo del hilo entra por `_guardar_llegada`. El QR y la transferencia que detecta el cobro también se anotan ahí. La columna Ticket sale de `vinculo_mp`. Con el monitor abierto se vuelve a leer cada segundo: el ticket asociado aparece sin salir de la pantalla.

**Historial largo y veredicto:** otra rama, `src/motor_cobros_digitales/` (ver su `plano.md`). Guarda cada pago en `mp_pagos` de la tienda, recupera lo que entró con la PC apagada, enlaza ticket ↔ id de pago y dice si el cobro digital es verdadero. Este monitor no espera por él.

`Admin10MP.ultimo_pago_detectado` lo escribe `EscuchaMP.publicar`. El cobro lo lee para cerrar la transferencia si el monto coincide.

## Qué no cambiar

No pedir el token en esta pantalla. No abrir un segundo hilo de escucha. No volver a simular un pago ni a importar el CSV oficial desde acá: el historial sale de la API.
