# Motor de descuentos / promociones

## Frente

Hub admin «Motor de promociones». Cada tarjeta abre un módulo aislado; al volver se destruye.

| Módulo | Qué hace | Qué no hace |
|--------|----------|-------------|
| Ofertas por producto | Carga promo de caja (cant+precio) y relámpago para TV | No imprime PDF. No toca TV. No edita costo ni stock |
| Combos | Varios artículos, un precio | Independiente de ofertas |
| Publicidad TV | Qué producto entra en cartelería | No cambia precios |
| Imprenta / PDF | Solo PDF para clientes | Lee ofertas; no las edita |
| Mayoreo | Global: Inventario + Promedios jefe (`MotorMayoreo`) | No es oferta de cartelería |

Tema claro (`#F8FAFC` / blancos). No usa `styles.qss` del cajero.

## Fondo

- Entrada: `hub/vista.py` → `Admin2Ofertas`
- Ofertas: `ofertas/` — `cant_oferta` + `precio_oferta` = regla de caja; `precio_oferta_relampago` + `limite` + `ventas` = flash con cupo (se apaga solo). Precio lista editable. Sin oferta promedio.
- Tras cobrar flash: `MotorOfertas.consumir_relampago` desde `persistir_cobro`; si agota, broadcast `PRECIOS_ACTUALIZADOS`
- Mayoreo: `mayoreo/motor.py` — `MotorMayoreo`; lo usan admin Inventario y jefe Promedios
- Tras guardar oferta: invalida catálogo y puede broadcast `PRECIOS_ACTUALIZADOS`
- PDF: `imprenta/` + `creador_pdf_global`
- Costo / stock: Inventario

No romper el aislamiento entre tarjetas del hub ni mezclar impresión con edición de promo.
