# Hilo de abastecimiento

Motor chico e independiente. Le pregunta al motor principal de inventario y no sabe armar el pedido.

## Qué hace la carpeta
Aísla la pregunta. Si el inventario no contesta, abastecimiento sigue con lista vacía.

## Qué función, con el nombre real
* `preguntar_alarma()`: llama a `MotorPlanilla.leer()`. No reescribe la planilla y no lee `productos`.
* `HiloReposicion`: hilo de la pantalla. Si ya hay un pase, o la lectura es local, no espera los 8 segundos de la maestra. Si está offline espera 0,4 s. No prende ese hilo y no reescribe la hoja.

## Cómo funciona, en el orden en que corre
1. La pantalla arranca `HiloReposicion`. No llama al inventario ella.
2. El orquestador pide faltantes al detector.
3. El detector llama a `preguntar_alarma()`.
4. `preguntar_alarma()` lee `planilla_reposicion`. Si tira error, devuelve `[]`.
5. El hilo emite el resumen. La pantalla solo pinta.

## Qué devuelve cuando falla
`preguntar_alarma()` devuelve `[]`. `HiloReposicion` emite `{}`. No hay excepción hacia la ventana.

## Qué no debe cambiar una mejora futura
* No importar `MotorCatalogo` desde el detector, el enlace ni la pantalla.
* No consultar `productos` desde este hilo. La regla sigue en `src/motor_inventario/alarma`.
* No correr la pregunta en el hilo de la ventana.
