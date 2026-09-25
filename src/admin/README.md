# Admin

Tema claro. En una pantalla vieja tiene que verse nítido y moverse sin tirones.

Al tocar un módulo de admin, se aplica esto:

- Color plano. Sin degradé, sin `rgba` y sin `QGraphicsDropShadowEffect`.
- Letras marcadas: título `#0F172A`, secundario `#1E293B`, tamaño 15 px, peso 600 o más. No usar gris `#94A3B8` ni `#64748B` para texto.
- Fondo `#F8FAFC` o blanco. Borde de 1 px `#CBD5E1`.
- El botón de acento es un solo color, por ejemplo `#2563EB`.
- No animar sombras ni pulsos que repinten la pantalla.

`theme_manager.apply_to_admin` ya pone esa base. Un estilo propio del módulo no la tapa con gris fino ni con sombra.

El cajero no usa esta hoja. Sigue oscuro, en el paso 5.
