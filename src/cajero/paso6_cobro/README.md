# Paso 6 — cobro

La ventana de cobrar. El gris tapa el paso 5. `paso6_cobro.py` arma la ventana.

La punta de esta rama es `punta del piramide.md`. Cada carpeta de adentro tiene su README.

El despacho de medios está en `motor_pagos/motores/__init__.py`, diccionario `REGISTRO`. Lo usa `MotorPrincipalCobros.iniciar_transaccion`.

Al abrir el cobro no se lee `clientes`. Esa lista entra en `_asegurar_lista_clientes`, la primera vez que se abre Fiado o Clientes.
