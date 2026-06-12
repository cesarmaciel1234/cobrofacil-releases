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
        lay.addWidget(modulo)
        lay.addStretch()
