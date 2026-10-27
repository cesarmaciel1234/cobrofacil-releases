# MercadoPago Core

This module provides a modular architecture for MercadoPago integration, replacing the legacy `mercadopago_integracion.py`.

## Files:
- `api_client.py`: HTTP a Mercado Pago. Una sola `requests.Session` (`MPApiClient.sesion`) para reusar TLS. No volver a `requests.put` suelto: el QR se demora en el handshake.
- `point_service.py`: Handles payments using MercadoPago Point devices. Manda el monto por `tarjeta_en_cobro/envio.py` para que la terminal conectada cobre con tarjeta. No activa QR en la terminal. El QR en pantalla es `paso6_cobro/qr_en_cobro/`. La espera es el cartel `EsperaPoint` de `aviso_en_cobro/`, con Cancelar. No abre `MPPollingDialog`.
- `qr_service.py`: Ventana vieja del POS. El cobro de QR ya no la abre. No la vuelvas a enganchar al clic de QR ni a Enter.
- `polling_service.py`: Handles polling and verification of MercadoPago transfers. La búsqueda de pagos usa `fecha_busqueda_mp`: `2026-09-24T12:35:50.000-03:00`. No vuelvas a `isoformat()` con `Z`. El rango es de 3 minutos (`en_ventana`). No busques transferencias de hace una hora. El último monto no pregunta si cerrar: si coincide, registra. Si la última no tiene ticket, el cartel ofrece «Asociar»: la diferencia queda en redondeo o recargo y ese cobro no se vuelve a usar. Si ya tiene ticket, el cartel dice que no hay nueva transferencia. La escucha mira Mercado Pago cada 2 segundos. El token sale de la config del TPV, el mismo que el monitor de admin. El aviso con sonido se prende con `mp_aviso_sonido` en `src/services/mp_escucha.py`.
- `ui_dialogs.py`: Contains the UI dialogs for waiting and polling for payments. El Point no abre `MPPollingDialog`: la espera es el cartel de `aviso_en_cobro/`.

## Usage:
Import the respective service class and instantiate it with the parent component to call the needed methods.

## Token (brecha de etapa)

El `mp_access_token` se carga en Admin → Terminales TPV y queda en la config de la estación. La caja lo necesita en el local para QR y Point. Más adelante lleva código. No lo saques de Admin ni lo pidas en cada cobro. Detalle: `paso6_cobro/decisiones.md`.

## Qué no cambiar

`PointService.procesar_pago_mercadopago_point` llama `config._load_config()` antes de leer `mp_access_token` y `mp_device_id`. `config.get` devuelve la memoria. No recarga el archivo. Esas llamadas se quedan, también en `Paso6Cobro._tpv_point_listo` y `_tpv_qr_listo`.

Un 201 de `/v1/orders` con `status: created` no es monto en el Point. `enviar_monto` espera `at_terminal`. Si sigue en `created`, cancela y avisa `otra_cuenta`.
