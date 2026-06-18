from src.vistas.proveedores import ModuloProveedoresUnificado

class VistaProveedoresMixin:
    """
    Mixin para la Pestaña de Proveedores en el Perfil Jefe.
    Ahora utiliza el módulo visual unificado, inyectando su propia base de datos (SQLite).
    """
    def _build_tab_proveedores(self):
        lay, _ = self._page()
        
        # Instanciar el módulo unificado pasándole el perfil y la BD del Jefe
        # self._db es el engine SQLite de JefeContabilidad
        modulo = ModuloProveedoresUnificado(parent=self, perfil="jefe", db_jefe=self._db)
        self.modulo_proveedores = modulo
        lay.addWidget(modulo)
        lay.addStretch()

    def _load_proveedores(self):
        # Cuando se cambia a esta pestaña, podemos forzar al submódulo a refrescar datos si es necesario
        if hasattr(self, 'modulo_proveedores') and hasattr(self.modulo_proveedores, 'cargar_datos'):
            self.modulo_proveedores.cargar_datos()
