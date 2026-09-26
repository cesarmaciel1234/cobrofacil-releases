# Centro de cobranza

La oficina de los créditos. La venta no se decide acá: el paso 5 vende, el paso 6 cobra, y este módulo es el garante que le dice al cobro si esa venta a cuenta puede registrarse.

```
clientes_fiado/
  plano.md
  cerebro/                 la única puerta
  garante/                 el ok entre la venta y el cobro
    orden/                 OrdenCobro
    despacho/              entregar → ejecutar_comun
    fiado/                 puerta por DNI
    cuenta_corriente/      puerta por nombre
  oficina/                 fichas, deudas, abonos, saldos
    cuenta/                MotorCuenta
    por_cobrar/            quién debe
    cobradas/              el abono
    saldos/                cupo y disponible
    cartel/                saludo de la confirmación
  agentes/
    wasap/                 rumbo. Hoy no envía
  interfaz/
    cobro/                 la hoja del mostrador
      medios/              efectivo, transferencia, tarjeta, QR, mixto y cerrar.py
    admin/                 el guardado de la pantalla clara
  motores/                 reexporta, para no romper el camino viejo
  ordenes/                 reexporta, para no romper el camino viejo
```

Fiado y Cuenta corriente son la misma cuenta. En el cobro siguen siendo dos teclas: Fiado pide el DNI y Cuenta corriente pide el nombre. La clave que se guarda en la venta no se renombra: `Fiado` y `Clientes`.

La pantalla pintada de admin sigue en `src/admin/clientes`. El tema claro no se mueve acá.

## Frente

En el cobro, Fiado y Cuenta corriente usan la hoja del cobro. Fiado solo toma el DNI, en números. Si el cupo no alcanza, el cartel del cobro pide el PIN de 4 dígitos de un admin. Si coincide, esa venta pasa y el cargo dice excepción. Si no, la venta no se carga. Al confirmar, el hueco de arriba dice «Hola» y el nombre, o «Sin datos» si admin todavía no lo cargó. `oficina/cartel/` arma ese texto. Si un dato no carga, el cobro sigue. Cuenta corriente, al escribir, lista los nombres parecidos y debajo el DNI. El primer Enter, si está bien, muestra saldo y disponible, limpia el campo y pide confirmar. El segundo Enter registra. El cartel no repite el monto ni trae Cancelar. Esc vuelve a los medios. Si el DNI ya está cargado, Fiado cruza con ese cliente. El Express nuevo solo se crea si no existe.

En el historial, la auditoría y el reporte del jefe, esa venta aparece como un medio más: el campo `metodo_pago` dice `Fiado` o `Clientes`. El jefe no tiene una lista aparte.

En admin, alta, edición, límite, abono, lista e historial se ven igual. El guardado entra por el cerebro. En la caja, el abono de F6 también entra por el cerebro. Al confirmar, la ventana llama a `interfaz/cobro/medios`: efectivo, transferencia, tarjeta, QR o mixto. El mixto reparte el abono en dos de esos medios. F6 no arma ese cobro en la venta. La hoja `ingresar_efectivo/fiado/cobro/` pide el PIN y llama a los motores: el QR con `pedir_qr_pos`, la tarjeta con `enviar_monto`. El código se dibuja en F6. Después `medios/cerrar.py` asienta. Si fallan, no tiran y la venta sigue. Esa puerta no llama al paso 6 y el paso 6 no la importa. El movimiento queda firmado como Cajero o Admin, con el nombre y el medio entre paréntesis. Solo el efectivo entra al cajón.

El agente de WhatsApp no se ve. No hay botón ni envío.

## Fondo

`cerebro/cerebro.py`, objeto `cerebro`. La pantalla no llama a un motor.

El paso 6 es el cobro. `MotorFiado.ejecutar` y `MotorClientes.ejecutar` solo hacen `cerebro.cobrar`. No preguntan de dónde vino el ok ni quién es el cliente: reciben el resultado. Siguen en `REGISTRO`. No validan el efectivo ni la tarjeta.

`garante/fiado/motor.py`, `MotorFiadoExpress.autorizar`, y `garante/cuenta_corriente/motor.py`, `MotorClienteExpress.autorizar`, arman `OrdenCobro`. Si `ok` es falso, no hay venta. `garante/despacho/despacho.py`, `entregar`, llama `ejecutar_comun`. No abre Point, ni QR, ni la escucha de transferencia. El cargo de la deuda va en la misma transacción que el ticket, en `src/base_de_datos/repos/ventas.py`, `_aplicar_fiado`.

La oficina no registra esa venta. `oficina/cuenta/motor.py`, `MotorCuenta`, lee y escribe `clientes` y `cuenta_corriente`. `oficina/cartel/motor.py`, `MotorCartel.armar`, llena el saludo. `SubmotorNombre` pone «Hola» o `Sin datos`. `SubmotorSaldos` pone la deuda y el disponible. Si uno falla, el otro igual devuelve. `por_cobrar` es `listar_con_deuda`, `ultimo_cargo` y `movimientos`. `cobradas` es `abonar`. `saldos` es `credito_disponible` y `limite_excedido`. El garante consulta esos saldos antes del ok.

`abonar` lee la deuda y anota el `ABONO` en la misma transacción, con `medio_pago`, `perfil` y `registrado_por`. Si el movimiento no queda escrito, la deuda no cambia y devuelve `(False, 0.0, "")`. `abonar_caja` arma la descripción `Cajero Nombre (Efectivo)`. El efectivo se anota en `movimientos_caja` como `Pago de clientes`. Si ese ingreso no entra, el admin avisa que la cuenta sí bajó y la caja no. El corte lo muestra aparte, dentro del efectivo esperado.

`oficina/cuenta/cuadre.py` lista las ventas `COMPLETADA` de Fiado o Clientes que no tienen `CARGO`. En admin, la franja ámbar abre esa lista. Cargar escribe el cargo en el cliente cuyo nombre coincide con uno solo. Si la venta quedó guardada como `Express` y el DNI, la carga en la ficha que ya tiene ese DNI. Cancelar el ticket llama `_anular_cargo` en la misma transacción: baja la deuda y deja una fila `ANULACION`. El cupo se vuelve a mirar dentro de la venta, con la ficha bloqueada. Si otra caja ya usó el cupo, la venta no se guarda. Una excepción de PIN o un ticket que ya se vendió (`ya_vendido`) no frena ese control.

La tabla `clientes` no se lee al abrir el cobro. `Paso6Cobro._asegurar_lista_clientes` llama `cerebro.listar` la primera vez que se abre Fiado o Clientes.

El SQL de alta express sigue en `ClienteRepository`. El motor de cuenta lo usa. `registrar_abono` termina en `cerebro.abonar`.

`agentes/wasap` no tiene cliente ni token. No lo llama el cobro.

## Qué no cambiar

No cargues `clientes` en el `__init__` del cobro.

No metas este cerebro en `validar_monto_suficiente`.

No hagas que el motor de fiado del paso 6 llame al de tarjeta, ni al revés. El paso 6 solo pide el ok.

No guardes la venta desde la hoja ni desde un diálogo. La hoja identifica. La orden ok guarda.

No renombres la clave `Clientes` a «Cuenta corriente» en la venta. El menú ya dice Cuenta corriente. El medio guardado sigue siendo `Clientes`.

No conectes el agente de WhatsApp al cobro ni a la venta.
