# Clientes en admin

Pantalla clara. Lista, alta, ficha, límite, abono e historial. Abonar abre el Centro de Cobranzas de F6 y registra con `cerebro.abonar_caja`. En el historial, el lápiz verde carga un saldo manual por `cerebro.cargar_manual`. El lápiz amarillo edita la ficha.

La tarjeta Cobros suma los abonos. El botón Planilla de cobros abre la grilla: fecha, cliente, DNI, monto, medio, perfil, quién cobró y saldo. El medio es el de «¿Con qué paga?»: Efectivo, Transferencia, Tarjeta o QR.

Si hay ventas Fiado o Clientes completadas sin cargo, aparece una franja ámbar. CUADRAR abre la lista. Cargar en la cuenta escribe el cargo solo cuando el nombre de la venta coincide con un solo cliente. Si el abono es en efectivo y la caja no lo anota, el aviso dice que la cuenta sí bajó.

El guardado no está en esta carpeta. Entra por `src/clientes_fiado`, objeto `cerebro`. El plano está en `src/clientes_fiado/plano.md`.

`dialogo_recalculo_fiado.py` solo analiza cargos. No escribe la deuda.
