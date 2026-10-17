# Temas de la TV

Qué hace: cinco vestuarios. Cada carpeta tiene `colores.css` y `estilos.css`.

Qué función: `loadTheme` en `la_cara_web/app.js` pone el `href` de `#theme-colors` y `#theme-styles`.

Cómo funciona: Admin → Configuración elige apple, temu, premium, black o blackfriday. Guardar llama `aplicar_config_tv_memoria`. El próximo `/api/state` trae `config.carteleria_theme`. Si el nombre ya está en `dataset.loaded`, no toca los `<link>`. Alias: `auto` y `negro_temu` → premium. La carpeta `negro_temu/` queda de respaldo; la cara no la carga.

Qué no debe cambiar: no armar de nuevo las columnas. No mezclar estas hojas con `src/styles.qss` del cajero.