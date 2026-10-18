# Estado HTTP

Qué hace: arma el JSON de `/api/state`.

Qué función: `EstadoMixin._publicar_estado` / `get_web_state`.

Cómo funciona: `_publicar_estado` copia config, precios y paneles desde memoria (`solo_memoria`): no abre MariaDB en el hilo de la pantalla. Si armar falla, deja el snapshot anterior. `get_web_state` nunca devuelve `None`. Si el tema en cache (`aplicar_config_tv_memoria` / `_leer_config_carteleria`, 20 s) no es el del snapshot, pisa solo `config.carteleria_theme` y no recalcula paneles. Si MariaDB falla al guardar, Admin llama `invalidar_cache_config_tv` para no dejar un tema que no se grabó.

Qué no debe cambiar: el HTTP de Chrome no recalcula paneles. `precios` tope 96. El catálogo completo queda en `rows_precios`.
