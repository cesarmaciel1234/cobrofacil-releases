# Contabilidad

ERP del jefe. La base es `contabilidad_jefe.db`, aparte de la tienda. La abre `get_jefe_db_path()` cuando se muestra `JefeContabilidad`.

`PAL` en `shared_globals.py` lee el tema global día/noche. No importa `theme_pro.py`.

Las vistas son mixins: resumen, ingresos, gastos, proveedores, préstamos, cheques, tarjetas, inversiones, costos fijos, historial y reportes. Las junta la clase `JefeContabilidad`.
