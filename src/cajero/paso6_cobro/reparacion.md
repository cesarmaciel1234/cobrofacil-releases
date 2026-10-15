# Reparación del cobro (paso 6)

Leé esto antes de tocar velocidad, ESC, QR, buscador o login. Si un síntoma vuelve, aplicá la fila. No inventes otro camino.

## Qué no romper (leyes)

- `Paso6Cobro._tpv_qr_listo` y `_tpv_point_listo` siguen con `config._load_config()` antes del token. `config.get` no recarga el disco.
- El pedido del QR **nunca** corre en el hilo de la UI. `pedir_qr_pos` va en un `Thread`.
- El cobro de QR **no** llama `asegurar_pos_qr`. Crear store/POS es de Admin → Terminales TPV.
- El F5 del cobro se retiró. PIN de cobranza apagado. PIN solo si el cupo no alcanza. F9 sin PIN: ver `decisiones.md`.
- Cobranza nunca manda un importe ≤ 0 a un medio. Con saldo a favor se cobra el ticket.
- ESC en la grilla (página 0) cierra al carrito. ESC con un medio abierto vuelve a la grilla **sin** MariaDB y **sin** recargar config. El medio queda vacío: volver a entrar no trae el importe. Esc en el casillero llama `_esc_un_paso`.
- `Paso6Cobro` se reusa: `_precalentar_cobro` en el paso 5 + `preparar_para_venta`. El import de `Paso6Cobro` queda adentro del método del paso 5.
- El buscador de clientes reusa 5 filas. No `deleteLater` ni recrear widgets por tecla.
- Búsqueda de producto: mínimo 3 letras, inicio de 1.ª o 2.ª palabra. Código de barras es exacto, no `LIKE %x%`.
- No tocar `src/utils/qt_dpi.py`. No unificar el tema oscuro del cajero.

## Síntoma → arreglo

| Se ve | Causa que ya dimos | Arreglo |
|---|---|---|
| El cliente ya pagó y el ticket no cierra | Se preguntaba `/v1/payments/search` cada 3 s (índice lento, recorte de fecha, GETs apiladas) | `pago_aprobado` lee la orden del POS, después merchant_orders. Panel cada 800 ms, una GET a la vez. |
| QR no sale y pide foto con TPV verde | Faltan `mp_user_id` y `mp_qr_pos_external_id` | Configurar en Admin → Terminales TPV. No crear el POS desde el cobro. |
| QR tarda otra vez tras un cobro | Se perdió `requests.Session` o el cache `_cuenta_cache` | Restaurar `MPApiClient._sesion` y `_cuenta_cache` en `qr_en_cobro/pedido.py`. |
| ESC congela | `salir_a_metodos` consultaba DB o `config._load_config` | `rutas_de_cobro/salida/proceso.py` solo suelta timers/Point/QR y página 0. |
| Esc y al volver a Mixto cobra el importe anterior | El casillero no llamaba Esc; la cuenta mixto no vaciaba | `_esc_un_paso` en el filtro de teclas. `salir_a_metodos` vacía mixto, efectivo y cliente. |
| F12 tarda / cobro se crea cada venta | Se descartó el diálogo precalentado | `preparar_para_venta` en `paso6_cobro.py`. No `new Paso6Cobro` en cada F12. |
| Buscador producto lento o pega en el medio del nombre | `LIKE '%texto%'` o `SELECT *` en UI | `carrito_service.py`: 3 letras, prefijo de palabra. Código exacto. |
| Buscador clientes rápido y después se congela | Recrear 5 widgets o emitir todo el índice por señal | Motor en RAM + lock. Emitir solo 5. Filas reusadas. |
| Flecha arriba/abajo en cobranza congela | `QFrame:hover` + `enterEvent` + `setStyleSheet` en cada flecha (bucle de estilo) | Filas fijas. Sin `:hover`. `marcar()` solo si cambió. Auto-repeat ignorado. |
| Enter del login tarda | Segunda query a `usuarios` | `AuthController.listar_credenciales` + `authenticate(..., cache=)` en `inicio_y_perfiles`. |
| Caja no arranca, IndentationError cash_drawer | `_init_opos` mal indentado | `src/hardware/cash_drawer.py`: `_init_opos` al nivel de la clase. OPOS lazy. |
| Señal de red tras cerrar | emit sobre QObject borrado | `network_engine`: `except RuntimeError`. |
| Cobranza arma QR/Point con $-2.600 | Saldo a favor sumado al ticket | Por defecto el ticket. Solo Deuda / Liquidar Todo si la deuda es > 0. `pedir_qr_pos` rechaza monto ≤ 0. |
| Cajón no abre en efectivo/mixto con casillero marcado | `post_cobro` pasaba un 13.er argumento (TypeError, se tragaba ticket y cajón). Mixto (Cliente) no coincidía con `"Mixto"`. El kick iba solo dentro del ticket y el spooler lo come. | Abrir con `drawer_manager.abrir` aparte. Nombre del medio por prefijo. Aceptar `condiciones_ticket_custom`. |
| F6 ficha del cliente + flecha derecha abre Cambio/Otros | Un solo diálogo juntaba F2 y F6 | F6 es `f6_centro_cobranzas/dialogo.py`. F2 es `ingresar_efectivo/dialogo.py`. |

## QR — camino vivo

1. Al armar `PanelQrCobro`, un hilo llama `precargar_conexion`: `_load_config`, cache de user/POS, TLS a `users/me` (3 s).
2. Al elegir QR, `_tpv_qr_listo` hace `_load_config` (luz).
3. `mostrar` pinta «Buscando…» y pide `pedir_qr_pos` en hilo.
4. `pedir_qr_pos` hace `_load_config`, lee token, usa `_cuenta_qr` (memoria). PUT instore 3,5 s. Si no hay `qr_data`, POST preferences 3,5 s. PNG chico (`box_size=4`, `border=1`, `ERROR_CORRECT_L`).
5. Pintar con `FastTransformation`. Al quedar el código, consulta al toque. Reloj 800 ms. Una GET en vuelo. `pago_aprobado`: orden POS → merchant_orders → payments/search.

Archivos: `qr_en_cobro/pedido.py`, `qr_en_cobro/panel.py`, `mercadopago_core/api_client.py`.

## Crédito / cobranza — camino vivo

`OrquestadorFiadoPiramidal` (no `PanelFiadoCobro`). Cancelar → `salir_a_metodos`. Crédito = `Clientes`. COBRANZA del paso 6 = `MasCredito` / `PanelCobranza`. F6 = centro del paso 5.

`MotorCobranzaMedios` asienta el abono y avisa ok. El ticket lo cierra `MotorPrincipalCobros`. No son dos motores rivales: ver `decisiones.md`.

Con saldo a favor el casillero arranca en el ticket. Nunca un cobro negativo.

## Si un parche vuelve a meter `asegurar_pos_qr` en el cobro

Sacalo. Esa función vive en `src/services/mercadopago_instore.py` y solo la usa Admin. El cobro, si no hay ids, muestra foto.
