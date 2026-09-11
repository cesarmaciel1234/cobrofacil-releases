# Motor de publicidad TV (separado)

Publicidad **no es** el carrusel de ofertas ni la grilla de precios. Es un motor aparte que **inyecta** avisos encima de esas listas.

## Regla de negocio

| Qué | Dónde se decide | Valor |
| --- | --- | --- |
| Cada cuántas tarjetas/filas va un aviso | `PUBLICIDAD_CADA` en `publicidad_tv.js` | **2** |
| 1 o 2 productos marcados | `alarmaPocosAds()` | **urgencia**: borde naranja ↔ amarillo |
| 3 o más marcados | mismo | **normal**: sin destello |
| 0 marcados | `listarAds()` vacío | **no inyectar** nada |

No inventar avisos con “más vendidos”. Solo productos con `es_publicidad`.

## Qué no mezclar

- **Carrusel de ofertas:** solo productos con precio rebajado (`esOferta` / `leerPrecios` en `plata_y_texto.js`). Si no hay ofertas: “Sin ofertas activas”.
- **Grilla de precios:** todos los productos con precio; el aviso se inserta cada 2 filas.
- **Publicidad:** lista marcada (JSON/`publicidad_tv` + `motor_publicidad.marcar_lista`). Se clona con `slot_ad: true` y se mete entre las tarjetas.

Un producto puede ser oferta **y** publicidad. En el carrusel entra como oferta; cada 2 tarjetas se **vuelve a inyectar** como aviso.

## Archivos (por dónde trabajar)

### Cara web (inyección y pinta)

- `src/carteleria/lanzador_tv/la_cara_web/modules/shared/publicidad_tv.js` — **único** intervalo, pool, urgencia, `intercalateAds`.
- `src/carteleria/lanzador_tv/la_cara_web/modules/franja_oferta/franja_oferta.js` — carrusel: ofertas + `intercalateAds(ofertas, productos)`.
- `src/carteleria/lanzador_tv/la_cara_web/modules/columna2/columna2.js` — grilla: `tocaPublicidad` + `htmlTarjetaPublicidad`.
- `src/carteleria/lanzador_tv/la_cara_web/modules/columna2/tarjetas/tarjeta_publicidad.js` — HTML del aviso en grilla (`is-ad-alarm` si `alarma`).
- `src/carteleria/lanzador_tv/la_cara_web/css/precio_tv/alarma.css` — destello; la copia `aria-hidden` del ticker **no** anima (congela la TV).

### Backend (quién está marcado)

- `src/carteleria/motor_carteleria/motor_publicidad.py` — nombres/ids, MariaDB `publicidad_tv`, `publicidad_config.json`, `marcar_lista`.
- Lanzador TV publica `es_publicidad` en cada ítem de `/api/state` (`lanzador_directo.py` / `ui_lanzador_tv.py`).

Cambio de intervalo: **solo** `PUBLICIDAD_CADA`. No copiar “cada 2” en las columnas.

## Cómo tocar sin romper

1. No filtrar ofertas con `!esPublicidad` (eso saca el producto rebajado del carrusel).
2. No usar `box-shadow` animado en todas las filas del ticker.
3. No reconstruir el carrusel si la firma de tarjetas no cambió.
4. No meter publicidad en `src/cajero/`.
