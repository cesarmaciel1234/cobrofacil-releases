# Prompt UI — Terminal de mostrador (PyQt6)

Prompt reutilizable para aplicar mejoras visuales en el terminal de caja **sin reescribir el motor de ventas**.  
Implementado en `src/cajero/paso5_terminal.py` (v4.6.1+).

---

## Copiar y pegar

> Actúa como desarrollador experto en Python y PyQt6. Tengo la interfaz de un Punto de Venta minimalista para operación a alta velocidad. Los widgets ya existen; necesito solo fragmentos de código, sin reescribir el motor ni la lógica de ventas.
>
> Genera los fragmentos PyQt6 para estas tres mejoras:
>
> **1. Sombra en la barra de búsqueda**  
> Aplicar `QGraphicsDropShadowEffect` al `QLineEdit` principal (`txt_scan`):
> - `setOffset(0, 4)`
> - `setBlurRadius(10)`
> - Color negro con ~22% opacidad: `QColor(0, 0, 0, 56)`
> - Elevación sutil (nivel 2), sin glow neón.
>
> **2. Contraste en el cuadro de resumen lateral**  
> Cada fila (Cantidad, Total Venta, Pagos, Cambio) debe usar **dos `QLabel` en un `QHBoxLayout`**:
> - **Título** (ej. "CANTIDAD"): Segoe UI, ~12px, peso 600, color gris `#64748B`
> - **Valor** (solo el número): Segoe UI, ~16–17px, peso 800, color `#0F172A`
> - **Cambio** al cobrar: valor en verde `#059669`
> - Fila "AHORRO OFER" opcional, visible solo si hay descuento.
>
> **3. Zona muerta táctil en teclas F**  
> En el `QHBoxLayout` de atajos F1–F12: `setSpacing(8)`.
>
> Asume variables existentes: `txt_scan`, `lbl_side_*`, `_hints_layout`, `shortcut_buttons`.

---

## Fragmentos de referencia

```python
# 1. Sombra búsqueda
shadow = QGraphicsDropShadowEffect(self.txt_scan)
shadow.setOffset(0, 4)
shadow.setBlurRadius(10)
shadow.setColor(QColor(0, 0, 0, 56))  # ~22%
self.txt_scan.setGraphicsEffect(shadow)
```

```python
# 2. Fila resumen (título + valor)
row = QHBoxLayout()
row.setSpacing(8)
lbl_t = QLabel("TOTAL VENTA")
lbl_v = QLabel("0")
lbl_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
lbl_t.setStyleSheet(
    "font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; color: #64748B;"
)
lbl_v.setStyleSheet(
    "font-family: 'Segoe UI'; font-size: 16px; font-weight: 800; color: #0F172A;"
)
row.addWidget(lbl_t)
row.addWidget(lbl_v, stretch=1)
```

```python
# 3. Zona muerta táctil
self._hints_layout.setSpacing(8)
```

---

## Archivos relacionados

| Archivo | Rol |
|---------|-----|
| `src/cajero/paso5_terminal.py` | Terminal principal, `_build_side_summary_row`, `_style_side_labels` |
| `src/utils/qt_dpi.py` | Alturas escaladas (`TERMINAL_STATUS_H`, etc.) |
| `src/cajero/ui_components/terminal_ui_mixin.py` | Mixin alternativo (mismas métricas) |
