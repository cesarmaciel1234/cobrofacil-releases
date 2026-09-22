# Unidad de medida (cualquier rubro)

Sirve carnicería, textil, bar, almacén, etc.

```
unidad_medida/
  logica/     normalizar + formatear + politica (siempre cobra)
  rubros/     default por departamento
```

- El stock puede ser negativo: `-100 kilo`, `-12 metro`, `-3 litro`.
- No bloquea el cobro. Es rastro de materia prima / merma.
- Prioridad: `es_pesable` → `unidad` del producto → departamento → `unidad`.
