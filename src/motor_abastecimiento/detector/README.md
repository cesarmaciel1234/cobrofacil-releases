# Subcarpeta Detector (Detección de Faltantes y Quiebre de Stock)

## Qué hace la carpeta
Copia la planilla. No calcula la cantidad.

## Qué función, con el nombre real
* `obtener_productos_bajo_minimo()`: llama a `preguntar_alarma()` y copia `cantidad_sugerida`. No tiene otra cuenta.

## Cómo funciona, en el orden en que corre
1. Llama a `preguntar_alarma()`, que lee `planilla_reposicion`. Si la fila trae `cantidad_sugerida`, usa esa. Después lee `costo` y `precio` de esos id. No decide la alarma.
2. Copia `cantidad_sugerida`. Cero significa que la fila se muestra y no se pide.
3. El presupuesto del renglón usa el costo. Si el costo está en cero, usa el precio de venta. Si la fórmula de huevo ya tiene costo de reposición, ese costo de compra cubre el cero y no se usa el precio. El WhatsApp sigue usando solo el costo. El `motivo` viaja con el ítem: `reposicion`, `critico` o `sin_piso`.
4. Al final junta lo que tiene fórmula: un cajón de Huevo o un bulto de Mocho, Pecho, Media res, Cerdo, Pollo o Congelado. No suma los cortes.

## Qué devuelve cuando falla
* Si el inventario no contesta, registra el error y devuelve `[]`. La pantalla queda en cero, no se traba.

## Qué no debe cambiar una mejora futura
* La alarma la responde `src/motor_inventario/alarma`. Desde acá, `productos` solo se lee para el costo y el precio de los id que ya están en la planilla.
* No escribir `productos`.
* Las cuentas de bulto o fórmula, si existen, se quedan en este módulo o en el pedido. No se graban en la planilla ni en el inventario.
