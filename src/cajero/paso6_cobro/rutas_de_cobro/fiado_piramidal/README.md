# Fiado piramidal

Qué hace: Orquesta crédito y cobranza del Paso 6.

Qué función: `OrquestadorFiadoPiramidal.mostrar(monto, modo)` con `modo` `Clientes`/`Fiado` o `MasCredito`. `reiniciar` cierra sin base.

Cómo funciona: `QStackedWidget` — buscador → verde, rojo, alta o cobranza. ESC emite `cancelado`. Paso 6 llama `salir_a_metodos`.

Qué no debe cambiar: no volver a `PanelFiadoCobro` ni reactivar F5. No llamar `cerebro` en ESC.
