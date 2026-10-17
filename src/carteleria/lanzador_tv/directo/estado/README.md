# Estado HTTP

Qué hace: arma el JSON de `/api/state`.

Qué función: `EstadoMixin._publicar_estado` / `get_web_state`.

Cómo funciona: copia config, precios y paneles. Si armar falla, deja el snapshot anterior. `get_web_state` nunca devuelve `None`.

Qué no debe cambiar: el HTTP de Chrome no recalcula paneles. `precios` tope 96 (premium estable). El catálogo completo queda en `rows_precios`.
