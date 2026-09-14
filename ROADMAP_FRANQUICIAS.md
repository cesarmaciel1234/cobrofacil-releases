# ROADMAP COMPLETADO: Sistema de Franquicias Activo (ID Sharding)

## ¿Qué se implementó?
En lugar de una dolorosa migración a UUIDs que requería reescribir 250+ consultas de SQL, se optó por la estrategia de **ID Sharding (Desplazamiento de Rango Automático)**, utilizada por gigantes como Instagram y Twitter.

## ¿Cómo funciona?
1. En el archivo config.json de cada sucursal física, el dueño solo debe configurar el parámetro "sucursal_id": 2, "sucursal_id": 3, etc. (Por defecto siempre es 1).
2. Cuando el programa arranca, la base de datos detecta el número de sucursal.
3. Se adelanta artificialmente el motor de Auto-Incremento para que salte a un bloque de **1,000 Millones (1 Billón) de IDs por sucursal**.
   - **Sucursal 1:** Empieza en ID 1.
   - **Sucursal 2:** Empieza en ID 2,000,000,001.
   - **Sucursal 3:** Empieza en ID 3,000,000,001.
4. **Resultado:** Puedes tener múltiples sucursales totalmente offline haciendo ventas y emitiendo tickets. Luego, si fusionas sus bases de datos en un solo pendrive o servidor central, ¡JAMÁS chocarán las ventas porque sus IDs están a 1.000 millones de números de distancia entre sí!

## Dónde está el código:
src/base_de_datos/migrations/migrator.py -> _aplicar_sharding_franquicias()
