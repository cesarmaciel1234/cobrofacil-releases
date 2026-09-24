# Cajero

Base. Junta las ramas de la caja. No lleva `plano.md`. La nota de cada rama se llama `punta del piramide.md` y vive en la carpeta de esa rama.

Leé esto antes de diagnosticar o de proponer un corte.

## Ramas

| Carpeta | Qué abre | Ventana |
|---|---|---|
| `paso5_terminal/` | Venta | `paso5_terminal.py`, clase `Paso5Terminal` |
| `paso6_cobro/` | Cobro | `paso6_cobro.py` |
| `paso8_historial/` | Historial, F3 | `dialogo.py`, clase `DialogoHistorialDia` |
| `ingresar_efectivo/` | Ingreso, F6 | `dialogo.py` |
| `sacar_efectivo/` | Retiro, F5 | `dialogo_retiro.py`, clase `DialogoRetiroEfectivo` |

`cajero_activo.py` guarda la estación (cajero 1 o 2). No es una pantalla.

## Hechos medidos

`paso5_terminal.py` termina en la línea 2427. La clase `Paso5Terminal` tiene 81 métodos.

`parse_float_safe` está una sola vez, en ese archivo, fuera de la clase.

`Paso5Terminal._precalentar_cobro` importa `Paso6Cobro` adentro del método. En el ejecutable ese import es el que espera. Corre con `QTimer` después de pintar la venta. No va al tope del archivo.

`TerminalController` está en `paso5_terminal/logica/terminal_controller.py`. Arma `CarritoService`, `StockOfertasService`, `MovimientosCajaService` y `CierreRemotoService`. Esos servicios leen con `db_manager`. No hay `ProductoRepository`.

`REGISTRO` está en `paso6_cobro/motor_pagos/motores/__init__.py`. `MotorPrincipalCobros.iniciar_transaccion` despacha. Las claves son efectivo, tarjeta, crédito, débito, mixto, transferencia, qr, mercadopago, fiado y clientes.

`CobroController.validar_monto_suficiente` no abre la base. Suma montos. Es estático. Si no alcanza, devuelve `(None, None)`.

En `src/cajero` no hay comentarios `TODO` ni `FIXME`. En el historial, `TODOS` es el valor del filtro de método de pago. En el cobro, `MÉTODO` es el rótulo de la página.

`sacar_efectivo` no tiene `dialogo.py`. El ingreso sí: `ingresar_efectivo/dialogo.py`.

## Qué no proponer

No crear `plano.md` en `src/cajero`.

No partir `paso5_terminal.py` en `event_handlers.py`, `state_manager.py` ni `validators.py`.

No subir al tope los imports que están adentro de un método. El de `Paso6Cobro` y el del teclado virtual están así para que falte una pieza y la venta igual abra.

No cambiar los `except Exception` del terminal por `TypeError` y `ValueError`. Esos cortes dejan seguir la caja si una pieza no viajó en el ejecutable.

No agregar un repositorio al lado de `db_manager`.

No convertir `validar_monto_suficiente` en método de instancia para inyectarle la base.

No renombrar `punta del piramide.md` en un diagnóstico. Si se cambia el nombre, se hace en la rama y se actualizan los README que lo nombran.

## Parece un defecto y no se toca

`Paso5Terminal` define `hideEvent` dos veces. El que corre es el que esconde `teclado_virtual` si `HAS_KEYBOARD`. El de arriba, que manda el datagrama `HIDE` a `127.0.0.1:45680`, queda pisado y no corre. En este repositorio nadie escucha el puerto 45680. No borres el `hideEvent` del teclado. No los juntes en un solo método: eso vuelve a mandar `HIDE`.

`sacar_efectivo/README.md` nombra `dialogo_retiro.py`. No lo corrijas a `dialogo.py`. Ese nombre es el de `ingresar_efectivo/dialogo.py`.

`Paso6Cobro._tpv_point_listo`, `Paso6Cobro._tpv_qr_listo` y `PointService.procesar_pago_mercadopago_point` llaman `config._load_config()` antes de leer el token. `config.get` no recarga el disco. `config.reload` mira `_last_mtime`, y `get` no lo llama. Sacar esos `_load_config()` deja la luz del TPV con el token viejo.

En `seleccionar_item_busqueda`, `cant_multi` arranca en `1.0`. Si el texto `cantidad*código` no es un número, el `except` desnudo lo deja en `1.0`. En `_evaluar_combos`, el `except` desnudo salta un combo mal armado y la venta sigue. No los cambies por un `logger.warning` que altere la cantidad.

El bip del escáner está detrás de `AUDIO_ENABLED`. El `import winsound` de adentro del hilo se queda. No saques el hilo.

El bloque `if __name__ == "__main__":` al final de `paso5_terminal.py` solo corre si alguien abre ese archivo a mano. No es código de la caja. No lo borres y no lo envuelvas de nuevo: ya está envuelto.

## Producción

Esta sección es la nota de la caja para sacar una versión. No hace falta otro informe. No inventa una matriz de riesgo.

### Venta

`Paso5Terminal.__init__` arma estos relojes:

| Reloj | Cada | Método |
|---|---|---|
| `timer` | 1 s | `actualizar_reloj` |
| `search_timer` | un solo tiro | `_do_busqueda` |
| `autofocus_timer` | 150 ms | `asegurar_foco_escaner` |
| `stock_timer` | 5 min | `verificar_stock_minimo`, si `stock_alerta_activa` |
| `autoclose_timer` | 1 min | `verificar_autocierre`, si `cierre_auto_activo` |

El bip del escáner es un `threading.Thread` daemon en el alta del producto, si `AUDIO_ENABLED`. Hay otro bip igual en `paso6_cobro/widgets/cliente_express.py` y en `fiado_express.py`. No comparten estado de la venta.

F12 abre el cobro. `_precalentar_cobro` ya importó `Paso6Cobro` un segundo después de pintar.

### Cobro

`_abrir` el flujo de clientes y `_abrir_fiado_express_original` usan `while True` para los dos diálogos. Si el cajero cancela, hacen `return`. No quedan girando solos.

La venta se escribe en `persistir_cobro`, que llama `db_manager.guardar_venta_completa`. Cabecera, renglones, stock y fiado van en esa transacción. El plano está en `src/base_de_datos/plano.md`.

### Hardware y red en la venta

F7 llama `_leer_bascula`. El puerto (`puerto_bascula`, o `COM1`) se abre en un hilo aparte, a 9600, manda `P` y espera la línea con timeout 0,45 s. El puerto se cierra siempre. El resultado vuelve por la señal `bascula_leida` a `_aplicar_lectura_bascula`. Si el puerto falla, escribe `0.750*` en el escáner y muestra un aviso. Si no hay respuesta, escribe `1.250*`. El próximo producto entra con esa cantidad. `focusChanged` se conecta una vez, en `_enganchar_foco_teclado`, no en cada F7.

Un código numérico no dispara la búsqueda por nombre. Esa búsqueda espera 160 ms y solo corre si el texto tiene letras. Enter corta el timer.

`StockOfertasService.obtener_combos` recuerda la lista 15 s, ya con el JSON leído. Si no hay combos, el escaneo no recorre el ticket para buscarlos. Una línea nueva sin combo repinta esa fila y la anterior. Borrar un renglón sigue repintando el ticket entero, para que las rayas no queden corridas.

`_evaluar_combos`, cuando aplica un combo, manda un UDP `COMBO_TRIGGERED` al broadcast, puerto 37021, y cierra ese socket.

F12 abre el cobro sin leer la tabla `clientes`. Esa lista se carga la primera vez que se abre Fiado o Clientes (`_asegurar_lista_clientes`). `_pintar_luz_tpv` lee el config una vez. `_tpv_point_listo` y `_tpv_qr_listo` siguen leyendo el config cada uno cuando se cobra con Point o QR.

El `hideEvent` del datagrama `HIDE` al puerto 45680 no corre. Está en la sección de arriba. No se junta con el del teclado para «limpiar código muerto» en un pase a producción.
