# Servicios de cuenta corriente

Qué hace: Puente opcional a `cerebro.asentar_fiado`.

Qué función: `gestor_cta_cte.asentar_nueva_deuda`.

Cómo funciona: El flujo vivo no lo llama. La venta la cierra `MotorFiado`/`MotorClientes`. El abono lo asienta `MotorCobranzaMedios`.

Qué no debe cambiar: no hacer SQL directo acá.
