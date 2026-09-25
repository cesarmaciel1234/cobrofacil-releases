# Clientes en admin

Pantalla clara. Lista, alta, ficha, límite, abono e historial. Abonar abre el Centro de Cobranzas de F6 y registra con `cerebro.abonar_caja`. En el historial, el lápiz verde carga un saldo manual por `cerebro.cargar_manual`. El lápiz amarillo edita la ficha.

El guardado no está en esta carpeta. Entra por `src/clientes_fiado`, objeto `cerebro`. El plano está en `src/clientes_fiado/plano.md`.

`dialogo_recalculo_fiado.py` solo analiza cargos. No escribe la deuda.
