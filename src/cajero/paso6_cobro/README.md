# Paso 6 — cobro

La ventana de cobrar. El gris tapa el paso 5. `paso6_cobro.py` arma la ventana.

Si algo de velocidad o ESC se rompe, `reparacion.md` de esta carpeta. No inventar otro arreglo.

F9 sin PIN, PIN de fiado después, token en Admin: `decisiones.md`. No “arreglarlos” en este pase.

La punta de esta rama es `punta del piramide.md`. Cada carpeta de adentro tiene su README.

El despacho de medios está en `motor_pagos/motores/__init__.py`, diccionario `REGISTRO`. Lo usa `MotorPrincipalCobros.iniciar_transaccion`.

Al abrir el cobro no se lee `clientes`. Esa lista entra en `_asegurar_lista_clientes`, la primera vez que se abre Fiado o Clientes, por `cerebro.listar`.

Fiado y Clientes salen de `src/clientes_fiado`. El frente del cobro es `rutas_de_cobro/fiado_piramidal/`. El motor del medio solo pide la orden ok. No comparte lógica con los otros cobros.

Mixto encadena los medios en `mixto_en_cobro/`. No manda el Point antes de cubrir. El resto a cuenta no convierte la venta en Fiado. F6 cobra la deuda vieja. Detalle en esa carpeta y en Producción de `punta del piramide.md`.

Esc es un paso atrás y deja el medio vacío (`decisiones.md`, `rutas_de_cobro/salida/`). Volver al mismo método no cobra el importe anterior.
