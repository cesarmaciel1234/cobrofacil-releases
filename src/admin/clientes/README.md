# Clientes en admin

Pantalla clara. Lista, alta, ficha, límite, abono e historial. **Abonar** abre F6 (`perfil=Admin`) con la lógica de producción: paso 1 monto, paso 2 medio, efectivo pide billetes. El cobro se asienta una sola vez. Sirve con deuda 0: el excedente queda a favor. **Límite** cambia el cupo. **Editar** la ficha. **Recalcular** simula precios de hoy y un % de financiación, sin escribir la cuenta.

La tarjeta Cobros suma los abonos. El botón Planilla de cobros abre la grilla: fecha, cliente, DNI, monto, medio, perfil, quién cobró y saldo. El medio es el de «¿Con qué paga?»: Efectivo, Transferencia, Tarjeta o QR.

Si hay ventas Fiado o Clientes completadas sin cargo, aparece una franja ámbar. CUADRAR abre la lista. Cargar en la cuenta escribe el cargo solo cuando el nombre de la venta coincide con un solo cliente. Si el abono es en efectivo y la caja no lo anota, el aviso dice que la cuenta sí bajó. Tras un abono ok, el cartel usa el mismo texto del mensajero de cobro (`COBRO EXITOSO` con nombre, pago y saldo).

El guardado no está en esta carpeta. Entra por `src/clientes_fiado`, objeto `cerebro`. El plano de esta pantalla es `plano.md`. El crédito: `src/clientes_fiado/plano.md`.

En el historial del cliente, pulsar el número azul de Ticket muestra el desglose abajo, en la misma ventana. `ELIMINAR TICKET / DEUDA` marca el cargo `BORRADO` sin borrar el renglón. Ver `componentes/README.md` y `plano.md`.

La lista calcula los días de atraso con `cerebro.ultimos_cargos()` por lotes de hasta 500 IDs. Esto evita que, al abrir o filtrar la cartera desde una esclava, la pantalla espere una ida y vuelta a la maestra por cada cliente con deuda. No volver a llamar `ultimo_cargo()` dentro del ciclo que dibuja las filas: para esa lista se debe conservar la consulta agrupada.

`dialogo_recalculo_fiado.py` solo analiza cargos. No escribe la deuda.

Al pasar el mouse por el nombre se ve la huella: qué PC lo creó, quién y cuándo. El botón AUDITORÍA (`componentes/dialogo_auditoria_clientes.py`) lista cada alta, edición, límite, cargo, abono y fusión: fecha, PC, caja, usuario y por dónde llegó (directo, sin red, nodo). Solo lee `clientes_auditoria` (`src/clientes_fiado/oficina/huella/consulta.py`).
