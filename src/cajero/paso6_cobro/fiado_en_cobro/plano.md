# Plano: piezas visuales de fiado en el cobro

## Frente vivo

El orquestador de crédito no usa `panel.py`. Usa el buscador de esta carpeta:

- `ui/buscador_clientes/panel_buscador.py` — DNI o nombre, flechas, Enter.

El resto de `ui/credito_aprobado/` y `componentes_fiado/` pertenece al panel legado `PanelFiadoCobro`. Paso 6 no lo instancia.

## Fondo

Las consultas las hace `MotorBusquedaClientes` (`src/motores_empresariales/motor_busqueda_clientes/`). El asiento de abono está en `MotorCobranzaMedios`. El cierre de venta, en `motor_pagos/motores/fiado` y `clientes`.

## Qué no romper

No reenganchar `paso6_cobro.py` a `PanelFiadoCobro`. F5 no cobra desde este panel.
