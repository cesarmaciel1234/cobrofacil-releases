# Plano — panel fiscal / ventas digitales

La rama arranca acá. Índice 14 del stacked. El dashboard la muestra como «Panel fiscal» y el jefe la ve; el admin puro la oculta junto con reportes y contabilidad.

## Frente

`ventas_digitales_main.py`, clase `Admin14VentasDigitales`. Tickets digitales y cruce con cobros.

## Fondo

Lee ventas y pagos. No toca stock. El token de MP lo guarda Configuración / Terminal TPV, no esta pantalla.

## Ecosistema

Consulta cobros y tickets. Envía filtros. No mezcla inventario ni proveedores.
