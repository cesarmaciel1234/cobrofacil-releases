# Repositorios

## Qué hace

Capa de acceso a datos y consultas de entidad (`productos`, `clientes`, `productos_codigos_adicionales`). Aísla las consultas SQL de la Interfaz Gráfica y centraliza las reglas de lectura/escritura seguras sobre `db_manager`.

## Funciones

| Archivo | Clase | Rol |
|---|---|---|
| `producto_repository.py` | `ProductoRepository` | Consultas de producto por ID, PLU balanza, ofertas SOS y gestión multi-código (1 a N: DUN-14, bultos y packaging alternativo). |
| `cliente_repository.py` | `ClienteRepository` | ABM de clientes, límites de crédito, fiado express, y actualización de saldos. |

### Métodos Principales de `ProductoRepository`

- `obtener_por_id(producto_id)`: Trae el producto por su ID primario.
- `obtener_por_plu_balanza(plu_raw)`: Resuelve el producto pesable a partir del PLU incrustado en el código de balanza.
- `obtener_codigos_adicionales(producto_id)`: Devuelve la lista de códigos secundarios asociados al ID.
- `agregar_codigo_adicional(producto_id, codigo, tipo, factor_unidades, descripcion)`: Registra un nuevo código con validación de no duplicidad contra códigos principales y secundarios.
- `eliminar_codigo_adicional(id_registro)`: Borra el código secundario por su clave primaria.
- `buscar_por_codigo_adicional(codigo)`: Resuelve el producto principal y su `factor_unidades` cuando se escanea un bulto o código secundario.

## Cómo funciona

1. La UI o servicio invoca el método estático del repositorio.
2. El repositorio ejecuta la consulta a través de `db_manager.execute_query` o `execute_non_query`.
3. Devuelve diccionarios con los datos limpios o tuplas `(exito, mensaje)`.

## Si falla

- Si no existe el registro, devuelve `None` o `[]`.
- Si hay colisión de código o datos inválidos, devuelve `(False, "motivo del error")`.

## Qué no debe cambiar

No acoplar interfaces gráficas dentro de los repositorios. Mantener métodos puros y seguros compatibles con MariaDB y SQLite. En `src/cajero` el controller lee directamente con `db_manager` según su regla de aislamiento.
