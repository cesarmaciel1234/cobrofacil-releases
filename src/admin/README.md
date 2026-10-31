# Admin

Tema claro. En una pantalla vieja tiene que verse nítido y moverse sin tirones.

## Ecosistemas autónomos

Cada tile del dashboard es un módulo cerrado. El hub **no importa** motores ajenos: emite `request_screen(índice)` y se aparta. El módulo pide datos a su servicio o cerebro y envía el resultado (stock, costo, cobro, config). No reescribe la raíz de otro.

La raíz de inventario ya está: un producto, su stock y su costo. Fórmula, reposición, ofertas y auditoría calculan en su carpeta. Al catálogo le llega el número, no un id sintético (`formula:Pollo`).

| Tile | Índice | Rama | Qué pide / envía | Qué no toca |
|------|--------|------|-------------------|-------------|
| Nexus | 18 | `admin/nexus_admin` | métricas y ventas al cerebro | stock, SQL en la vista |
| Inventario | 2 | `ui_global/inventario_ui` | catálogo vía `InventarioService` | ofertas, fórmula |
| Ofertas | 3 | `motor_descuentos` | precios promo | stock, costo |
| Cierre | 7 | `admin/cierre` | arqueo al cerebro de caja | catálogo |
| Mercado Pago | 10 | `admin/mercadopago` | cobros al motor digital | token (vive en config) |
| Etiquetas | 8 | `admin/etiquetas_panel_ui` | productos para imprimir | no cambia precio |
| Configuración | 5 | `admin/configuracion` | `config.json` | no escribe `productos` |
| Red LAN | 6 | `admin/red_lan` | réplica maestra/esclava | no calcula stock |
| Hardware | 13 | `admin/hardware` | puertos locales | no el cobro |
| Clientes | 17 | `admin/clientes` | fiado / cargos | no el paso 6 del cajero |
| Proveedores | 11 | `proveedor_global` | remito; envía stock y costo | no mezcla ids de fórmula |
| Auditoría | 25 | `admin/auditoria_inventario` | conteo; SET de stock | no `guardar_producto` |

Reportes, contabilidad y panel fiscal no se muestran al admin puro: son del jefe. El cajero no usa esta hoja.

---

Al tocar un módulo de admin, se aplica esto:

Al tocar un módulo de admin, se aplica esto:

- Color plano. Sin degradé, sin `rgba` y sin `QGraphicsDropShadowEffect`.
- Letras marcadas: título `#0F172A`, secundario `#1E293B`, tamaño 15 px, peso 600 o más. No usar gris `#94A3B8` ni `#64748B` para texto.
- Fondo `#F8FAFC` o blanco. Borde de 1 px `#CBD5E1`.
- El botón de acento es un solo color, por ejemplo `#2563EB`.
- No animar sombras ni pulsos que repinten la pantalla.

`theme_manager.apply_to_admin` ya pone esa base. Un estilo propio del módulo no la tapa con gris fino ni con sombra.

Varios módulos a la vez: `ventanas_sueltas/` (mismo PID). No un segundo perfil admin.

El cajero no usa esta hoja. Sigue oscuro, en el paso 5.
