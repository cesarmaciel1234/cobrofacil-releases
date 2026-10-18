# Catálogo en memoria de la TV

Qué hace: convierte filas (dict o tupla) en productos que la cara puede pintar.

Qué función: `CatalogoMixin._aplicar_catalogo` / `_normalizar_productos`.

Cómo funciona: descarta sin nombre o sin precio. Marca publicidad. Si la lista nueva queda vacía y ya había productos, no los borra. No borra el índice de PNG en cada pulso: se renueva solo a los 20 s.

Qué no debe cambiar: no vaciar `rows_precios` por un sync fallido.
