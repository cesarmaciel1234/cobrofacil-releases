# Estado Crédito

Qué hace: Estado de la cuenta (hola, deuda o a favor), el resumen «saldo actual + interés nuevo = total estimado» y el paso 1: «¿Cuánto paga a la cuenta?». El paso 2 («Tocá cómo paga») queda arriba de los botones. `$ Personalizado` no cobra: el monto se escribe en el recuadro.

Qué función: `PanelEstadoCredito` en `panel_estado.py`. `lbl_historial` muestra hasta 4 líneas que trae el hilo de F6. Si el hilo no contesta, el label se oculta y PAGAR sigue.

Cómo funciona: Se instancia y se agrega al layout de `PanelFiadoCobro`. Provee propiedades públicas (`icono`, `estado`, `detalle`, `lbl_total_estimado`, `txt_monto_abono`, `btn_abono_libre`, `instruccion`) que el panel principal manipula para mostrar u ocultar componentes según el modo (buscando, confirmando, cobranza). El resumen viene del hilo de historial y no sustituye el cálculo transaccional del abono.

Qué devuelve cuando falla: No tiene lógica compleja que falle, delega eventos visuales.

Qué no debe cambiar una mejora futura: Los nombres de los atributos expuestos, ya que `PanelFiadoCobro` los mapea hacia sí mismo para no romper la compatibilidad externa. La falla del hilo debe dejar visible el error sin bloquear la hoja de cobranza.
