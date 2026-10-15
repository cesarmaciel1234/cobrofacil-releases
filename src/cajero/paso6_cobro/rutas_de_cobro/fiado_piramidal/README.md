# Fiado piramidal

Qué hace: Orquesta crédito y COBRANZA del **paso 6**. No es F6 (`f6_centro_cobranzas/`). Tabla: `src/cajero/README.md`.

Qué función: `OrquestadorFiadoPiramidal.mostrar(monto, modo)` con `modo` `Clientes`/`Fiado`/`MasCredito`. `MasCredito` es COBRANZA del paso 6 (`PanelCobranza`). `reiniciar` cierra sin base.

Cómo funciona: `QStackedWidget` — buscador → verde, rojo, alta o liquidación. ESC emite `cancelado`. Paso 6 llama `salir_a_metodos`. F6 del paso 5 es otro diálogo.

Qué no debe cambiar: no volver a `PanelFiadoCobro` ni rearmar un F5 de cobro. No llamar `cerebro` en ESC.
