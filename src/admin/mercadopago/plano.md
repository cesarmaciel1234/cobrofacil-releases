# Plano — monitor de Mercado Pago

La rama arranca en esta carpeta. La base es `src/admin` y no lleva plano.

## Frente

`mercadopago_main.py`, clase `Admin10MP`. Se abre desde el menú de admin. El título es **Auditoría de cobros digitales**. La grilla la arma `src/motor_auditoria_digital/` en un hilo aparte: cobros reales de MP, tickets digitales y F9. Si ese motor falla, la caja sigue y la pantalla cae al CSV local.

Arriba: volver, el título, el interruptor «Cajero silencioso» / «Con sonido», Actualizar y el estado. No hay campo de token, ni «Guardar e Iniciar», ni «Simular», ni importar un CSV a mano.

El cuerpo: bruto/neto vs tickets vs firmados vs sin firmar/F9 vs Cliente. Período Hoy / Semana / Mes / Año / Período. Las dos casillas viejas (cargas / omitidos) son **Firmados** y **Pendientes**. Las dos prendidas: lo que importa para AFIP. Solo Firmados: venta o cobranza con id MP. Solo Pendientes: SIN TICKET, SIN FIRMAR, F9. Cargas propias y omitidos no entran.

## Fondo

El token es `mp_access_token` de la configuración del TPV. Lo lee `EscuchaMP.token()` en `src/services/mp_escucha.py`. Esta pantalla no lo guarda.

**Token de tienda (nuevo):** la maestra, al guardar Terminal TPV, publica el token en MariaDB `configuracion` (`sync_tienda/mp_token`). La esclava lo trae sola al conectar y al abrir el monitor. No hay que pegar el token en cada notebook. Si aún dice SIN TOKEN, en la PC de caja (maestra) hay que Guardar una vez el Terminal TPV para publicarlo.

**Fuera de red:** el nodo portable lleva también `reportes/mercado_pago_sync.csv` y `reportes/mp_vinculos.json`. Al abrir el monitor o pulsar **Actualizar**, la copia del nodo se combina antes de pintar. **Actualizar** luego baja el mes actual vía API y sincroniza por ID al nodo; cada pago que llega en vivo también queda copiado. Se combinan pagos nuevos, cambios de omitido/restaurado y tickets asociados. Si no hay token o la API no responde, el monitor muestra la copia local; si el nodo configurado está desconectado, informa que la sincronización quedó pendiente.

Auditoría en la grilla: pago MP con ticket (firmado); pago MP sin ticket (`SIN TICKET`, horario para cámaras); venta QR/tarjeta/transf. sin pago (`F9 MANUAL`). Fiado, clientes y DNI no entran. MasCredito no se cuenta como digital. Las ventas se leen con tope de 5 s. Asociar en caja o sincronizar el nodo despierta el motor.

**Esclava:** ventas/stock = MariaDB. El historial MP (CSV) se baja con ese token vía API cuando hay conexión. `mp_vinculos.json` se mantiene local hasta sincronizar el nodo, que permite llevarlo y traerlo junto al historial.

`iniciar_monitor` llama `traer()` y después `EscuchaMP.asegurar()`. Es el mismo hilo que el cajero, `MPPollingThread` en `componentes/`. No se frena al salir del monitor.

`historial/sincronizar.py`, `bajar_mes`, baja los cobros aprobados del mes, de punta a punta. Actualizar y la apertura del monitor lo corren en `_BajadaMes`, fuera de la ventana: el estado pasa a ACTUALIZANDO y después vuelve a ESCUCHANDO. El botón pinta la grilla al toque, desde el archivo, aunque la bajada siga. Si la API no responde, queda visible la copia local con el estado SIN RED · COPIA LOCAL. La consulta lleva fecha de inicio y de fin; sin la de fin la API no devuelve pagos. La hora de la grilla es la de Argentina. Una transferencia recibida no se esconde con las cargas propias. Point y el QR llevan el mismo nombre que la app. `historial/archivo.py` los escribe en `reportes/mercado_pago_sync.csv`. Las tarjetas las arma `motor_auditoria_digital/cruces/totales`. Un pago nuevo del hilo entra por `_guardar_llegada`. El QR y la transferencia que detecta el cobro también se anotan ahí. La columna Ticket sale de `vinculo_mp`. Con el monitor abierto se vuelve a leer cada segundo: el ticket asociado aparece sin salir de la pantalla.

**Historial largo y veredicto:** otra rama, `src/motor_cobros_digitales/` (ver su `plano.md`). Guarda cada pago en `mp_pagos` de la tienda, recupera lo que entró con la PC apagada, enlaza ticket ↔ id de pago y dice si el cobro digital es verdadero. Este monitor no espera por él.

`Admin10MP.ultimo_pago_detectado` lo escribe `EscuchaMP.publicar`. El cobro lo lee para cerrar la transferencia si el monto coincide.

## Qué no cambiar

No pedir el token en esta pantalla. No abrir un segundo hilo de escucha. No volver a simular un pago ni a importar el CSV oficial desde acá: el historial sale de la API.
