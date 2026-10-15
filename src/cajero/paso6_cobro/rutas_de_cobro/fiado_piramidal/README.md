# Fiado piramidal

Qué hace: Orquesta crédito y cobranza del Paso 6.

Qué función: `OrquestadorFiadoPiramidal.mostrar(monto, modo)` con `modo` `Clientes`/`Fiado`. `MasCredito` se trata como crédito. `reiniciar` cierra sin base.

Cómo funciona: `QStackedWidget` — buscador → verde, rojo o alta. ESC emite `cancelado`. Paso 6 llama `salir_a_metodos`. La cobranza es F6.

Qué no debe cambiar: no volver a `PanelFiadoCobro` ni rearmar un F5 de cobro. No llamar `cerebro` en ESC.
