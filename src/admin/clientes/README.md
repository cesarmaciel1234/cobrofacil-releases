# Clientes en admin

Pantalla clara. Lista, alta, ficha, límite, abono e historial. Abonar abre el Centro de Cobranzas de F6 y registra con `cerebro.abonar_caja`. En el historial, el lápiz verde carga un saldo manual por `cerebro.cargar_manual`. El lápiz amarillo edita la ficha.

La tarjeta Cobros suma los abonos. El botón Planilla de cobros abre la grilla: fecha, cliente, DNI, monto, medio, perfil, quién cobró y saldo. El medio es el de «¿Con qué paga?»: Efectivo, Transferencia, Tarjeta o QR.

Si hay ventas Fiado o Clientes completadas sin cargo, aparece una franja ámbar. CUADRAR abre la lista. Cargar en la cuenta escribe el cargo solo cuando el nombre de la venta coincide con un solo cliente. Si el abono es en efectivo y la caja no lo anota, el aviso dice que la cuenta sí bajó. Tras un abono ok, el cartel usa el mismo texto del mensajero de cobro (`COBRO EXITOSO` con nombre, pago y saldo).

El guardado no está en esta carpeta. Entra por `src/clientes_fiado`, objeto `cerebro`. El plano está en `src/clientes_fiado/plano.md`.

En el historial del cliente, pulsar el número azul de Ticket de una fila `CARGO` abre el desglose de la venta. La lectura va por un motor independiente y se ejecuta fuera del hilo de interfaz. Ver `componentes/README.md` y `plano.md`.

`dialogo_recalculo_fiado.py` solo analiza cargos. No escribe la deuda.

Al pasar el mouse por el nombre se ve la huella: qué PC lo creó, quién y cuándo. El botón AUDITORÍA (`componentes/dialogo_auditoria_clientes.py`) lista cada alta, edición, límite, cargo, abono y fusión: fecha, PC, caja, usuario y por dónde llegó (directo, sin red, nodo). Solo lee `clientes_auditoria` (`src/clientes_fiado/oficina/huella/consulta.py`).
