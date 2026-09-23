# Punto de Venta Pro

Cómo se modulariza: `modularizacion.md`. Al mejorar un módulo se aplica esa forma. La auditoría de inventario arranca en `src/admin/auditoria_inventario/plano.md`.

Sistema completo y editable de Punto de Venta.

Características:
- Pesos argentinos ($)
- Productos por kilo y por unidad
- Pensado para carnicería
- Impresión térmica (estructura preparada)
- Guardado de productos y ventas
- Windows 11

Ejecución:
```
pip install -r requirements.txt
python main.py
```

Las imágenes de producto para cartelería se generan con `src/carteleria/creador_png/` y se guardan en `Catalogos/png_productos/`.
