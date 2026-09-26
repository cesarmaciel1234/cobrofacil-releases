# Fiado

Cobra deudas. La consulta está en `consulta.py`. El DNI lo normaliza `cerebro`. El listado y la ficha del cliente son dos zonas: al elegir uno, el listado se esconde y queda el nombre, el DNI y la deuda. Si vuelve a buscar, limpia el monto y la ficha. Al confirmar el importe, `cobro/pagina.py` pide el medio. El clic pide el PIN y corre el motor en el contenedor de esa hoja. No abre la venta. Después, F6 y el admin confirman el abono con `cerebro.abonar_caja`. Los colores en `paleta.py`.

`IMPRIMIR SALDO` saca tres números: saldo anterior, crédito y saldo. Al confirmar el abono sale el mismo ticket con el saldo guardado. El historial no se imprime acá.

Al volver al paso 5, el mensajero es el mismo de un cobro normal: `✅ COBRO EXITOSO — nombre · pago · saldo`, con el marco verde. Lo publica `medios/cerrar.avisar` al asentar.
