# Ofertas por producto

## Qué hace

Lista productos y deja cargar / quitar la promoción de uno. El panel edita precio de lista y reglas de promo. Costo y stock no se editan acá. No imprime carteles (eso es Imprenta).

### Oferta (cant. + precio)

Regla de caja: desde X unidades/kilos → precio oferta. Ej.: supremas desde 2 kg a $Y.

### Relámpago (precio flash + límite)

Precio más bajo que la oferta, con **cupo**. Mientras haya cupo, la caja cobra relámpago y la TV lo muestra. Contador: `Vendidos: 1 / 5`. Al llegar al límite se **apaga** el flash (`precio_oferta_relampago=0`), broadcast `PRECIOS_ACTUALIZADOS`, y la cartelería vuelve a lista/oferta normal.

Prioridad en caja: **mayoreo → relámpago (si cupo) → oferta ≥ umbral → lista**.

Límite 0 = flash sin tope (no se apaga solo; solo decorativo/manual).

Si el cupo restante es menor que el “desde” de la oferta (ej. vendieron 4 de 5 y desde=2 → queda 1), el flash **se apaga**: no deja 1 colgado que no completa el mínimo.

## Piezas

| Archivo | Rol |
|---------|-----|
| `vista.py` | `TallerOfertas`: filtro, splitter lista + panel, Activar/Quitar |
| `tabla.py` | `TablaOfertas`: Nombre, Precio, Oferta, Reglas, Stock |
| `editor.py` | Precio lista + promo + relámpago + contador de cupo |
| `motor.py` | `MotorOfertas`: aplica/limpia; `resolver_precio_venta`; `consumir_relampago` |

## Cómo corre

1. Hub abre `TallerOfertas`.
2. Activar → `aplicar_oferta` (reinicia ventas del cupo si hay relámpago/límite).
3. Caja cobra línea `⚡ [RELÁMPAGO]` → `persistir_cobro` → `consumir_relampago_en_items`.
4. Si cupo agotado → apaga flash + avisa red/TV.

## Si falla

Consumir relámpago no tumba la venta (try/except en cobro).

## Qué no debe cambiar

No reintroducir oferta promedio. No imprimir desde acá. Relámpago no reemplaza la regla “desde X” una vez apagado.
