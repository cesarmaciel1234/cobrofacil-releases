# Estado Crédito

Qué hace: Contiene los elementos visuales que muestran el estado de la cuenta (icono, estado, detalle) y los controles para ingresar un abono libre.

Qué función: `PanelEstadoCredito` en `panel_estado.py`

Cómo funciona: Se instancia y se agrega al layout de `PanelFiadoCobro`. Provee propiedades públicas (`icono`, `estado`, `detalle`, `txt_monto_abono`, `btn_abono_libre`, `instruccion`) que el panel principal manipula para mostrar u ocultar componentes según el modo (buscando, confirmando, cobranza).

Qué devuelve cuando falla: No tiene lógica compleja que falle, delega eventos visuales.

Qué no debe cambiar una mejora futura: Los nombres de los atributos expuestos, ya que `PanelFiadoCobro` los mapea hacia sí mismo para no romper la compatibilidad externa.
