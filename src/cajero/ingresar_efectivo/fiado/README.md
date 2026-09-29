# Fiado

Cobra deudas. La consulta está en `consulta.py`. El DNI lo normaliza `cerebro`. El listado y la ficha del cliente son dos zonas: al elegir uno, el listado se esconde y queda el nombre, el DNI y la deuda. Al elegir desde la lista, el foco va al monto y selecciona su contenido para reemplazarlo directamente. Si hay varios resultados, Enter lleva a la lista; flechas y Enter permiten elegir sin mouse. Si vuelve a buscar, limpia el monto y la ficha. El monto a abonar se confirma antes de elegir medio. Para efectivo, `cobro/pagina.py` pide aparte cuánto dinero recibió el cajero y muestra en vivo cuánto falta o sobra; al abrir indica el monto pendiente y si el recibido coincide muestra vuelto $0.00. Al confirmar ese recibido pide PIN y abre el cajón solo si se autoriza. Si se cancela el PIN, conserva el recibido en pantalla y no abre el cajón. Los otros medios piden PIN antes de iniciar su motor. No abre la venta. Después, F6 y el admin confirman el abono con `cerebro.abonar_caja`. Los colores en `paleta.py`.

`IMPRIMIR SALDO` saca tres números: saldo anterior, crédito y saldo. Al confirmar el abono sale el mismo ticket con el saldo guardado. El historial no se imprime acá.

Al volver al paso 5, el mensajero es el mismo de un cobro normal: `✅ COBRO EXITOSO — nombre · pago · saldo`, con el marco verde. Lo publica `medios/cerrar.avisar` al asentar.
