# Plano — monitor de Mercado Pago

La rama arranca en esta carpeta. La base es `src/admin` y no lleva plano.

## Frente

`mercadopago_main.py`, clase `Admin10MP`. Se abre desde el menú de admin.

Arriba: volver, el título, el interruptor «Cajero silencioso» / «Con sonido», Actualizar y el estado. No hay campo de token, ni «Guardar e Iniciar», ni «Simular», ni importar un CSV a mano.

El cuerpo son las cinco tarjetas, el buscador, el filtro de fecha y la tabla. El clic derecho omite un pago o lo restaura.

## Fondo

El token es `mp_access_token` de la configuración del TPV. Lo lee `EscuchaMP.token()` en `src/services/mp_escucha.py`. Esta pantalla no lo guarda.

`iniciar_monitor` llama `EscuchaMP.asegurar()`. Es el mismo hilo que el cajero, `MPPollingThread` en `componentes/`. No se frena al salir del monitor.

`historial/sincronizar.py`, `bajar_mes`, baja los cobros aprobados del mes. `historial/archivo.py` los escribe en `reportes/mercado_pago_sync.csv` y `leer` arma las tarjetas. Un pago nuevo del hilo entra por `_guardar_llegada`. El QR y la transferencia que detecta el cobro también se anotan ahí. La columna Ticket sale de `vinculo_mp`.

`Admin10MP.ultimo_pago_detectado` lo escribe `EscuchaMP.publicar`. El cobro lo lee para cerrar la transferencia si el monto coincide.

## Qué no cambiar

No pedir el token en esta pantalla. No abrir un segundo hilo de escucha. No volver a simular un pago ni a importar el CSV oficial desde acá: el historial sale de la API.
