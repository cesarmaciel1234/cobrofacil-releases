# Observabilidad operativa

## Qué hace la carpeta

Mide qué tan bien cubre un plan el consumo previsto y deja métricas simples para el panel del Jefe.

## Qué función, con el nombre real

* `cobertura(stock, ritmo)`: expresa cuántos días cubre el stock actual.
* `resumen(plan)`: cuenta acciones por estado y fuente.

## Cómo funciona

Lee el contenido de un plan; no escribe datos ni califica a una persona. Las métricas sirven para contrastar luego la decisión con la recepción y la venta real.

## Qué devuelve cuando falla

Valores neutros: cobertura cero o contadores vacíos.

## Qué no debe cambiar una mejora futura

No modifica la decisión original para ocultar un error de pronóstico.
