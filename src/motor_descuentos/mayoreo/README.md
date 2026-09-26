# Mayoreo

## Qué hace

Umbral de volumen global: desde `cant_mayoreo` → `precio_mayoreo`. Lo manejan más de un perfil (Inventario admin y Promedios jefe). No es oferta de cartelería.

## Función

`MotorMayoreo` en `motor.py`. La tarjeta del hub solo explica (`vista.py` → `PaginaMayoreo`).

## Cómo funciona

1. **Inventario:** edita mayoreo en el producto; la grilla muestra Cant. may. / P. mayoreo.
2. **Jefe → Promedios:** exportar llama `aplicar_desde_promedios`; sincronizar lee `obtener_por_nombre`.
3. **Caja:** si la cantidad alcanza el umbral, mayoreo gana sobre oferta.

## Si falla

`False`, dict en cero o lista vacía. Logger.

## Qué no debe cambiar

No escribir `precio_oferta` ni `precio_oferta_promedio`. Cartelería depende de Ofertas, no de mayoreo.
