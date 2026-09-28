# Leyes del Proyecto TPV PRO 2026 (Instrucciones para IA)

La forma de modularizar está en `modularizacion.md`, en la raíz.

Al mejorar un módulo, ofrecer y aplicar esa opción en el mismo cambio: la rama en su carpeta, `plano.md` donde arranca (frente y fondo), y `README.md` en cada subcarpeta con qué hace, qué función y cómo funciona.

No crear `regla_*.md` en la raíz. Antes de editar, leer el `plano.md` de la rama y el `README.md` de la subcarpeta.

## Escalado global — NO TOCAR

`src/utils/qt_dpi.py` fija `QT_SCALE_FACTOR` de **todo** el proceso (cajero, admin, jefe).

Si un sector se ve chico (letras, tiles, botones), agrandar **solo en ese módulo**: tipografía, `setFixedSize`, QSS locales. No subir el piso de `layout_scale` ni “arreglar” baja resolución desde `qt_dpi` para un pantallazo: escala toda la app.

Detalle: `src/utils/README.md` y `.cursor/rules/escalado-global-no-tocar.mdc`.

Antes de diagnosticar, editar o dar por lista una versión de `src/cajero`, leer `src/cajero/README.md`: las secciones «Parece un defecto y no se toca» y «Producción». Esa carpeta es base: no lleva `plano.md`. La nota de cada rama se llama `punta del piramide.md`. No borrar ni “juntar” lo que esa nota marca. No reemplazarla por un informe de riesgo nuevo.

Antes de diagnosticar o editar `src/jefe`, leer `src/jefe/reglas.md`. Esa carpeta es base: no lleva `plano.md`. El tema es el global (`estilo_dia.qss` / `estilo_noche.qss`). `theme_pro.py` está retirado. El sqlite del nodo portable no se reemplaza por `db_manager`.
