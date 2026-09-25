# Cerebro

`cerebro.py`, clase `CerebroClientesFiado`. El objeto `cerebro` es la única puerta.

Identifica por DNI o por nombre, mira el cupo en la oficina, da de alta, edita, fija el límite, abona y lista. `abonar_caja` es el abono del Centro de Cobranzas: lo llaman F6 y el botón Abonar del admin, imprime el ticket de saldo. `cartel` pide a `MotorCartel` el saludo y los números de la confirmación. Si un dato no carga, devuelve `Sin datos` y el cobro sigue. `autorizar` arma `OrdenCobro` en el garante. `cobrar` solo llama `entregar` si `ok` es verdadero.

Una pantalla no escribe `clientes` ni `cuenta_corriente` por su cuenta. El paso 6 no elige el cliente: pide `cobrar` y recibe el ok.
