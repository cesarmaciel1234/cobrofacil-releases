"""Índices fijos del QStackedWidget en MainWindow.

NO reordenar ni reutilizar índices libres sin revisar:
  - admin/dashboard/dashboard_main.py (tarjetas del dashboard)
  - inicio_y_perfiles/perfil_pantalla.py (roles)
  - Atajos F11 / pirámide de acceso
  - main_window.py (_screen_factories)

La fuente de verdad de fábricas es MainWindow. Este mapa tiene que
coincidir: un índice libre acá no puede tener widget allá.
"""


class Screen:
    ADMIN_DASHBOARD = 0
    CAJERO = 1
    INVENTARIO = 2
    OFERTAS = 3
    REPORTES = 4
    CONFIGURACION = 5
    RED_LAN = 6
    CIERRE = 7
    ETIQUETAS = 8
    CONTABILIDAD = 9
    MERCADO_PAGO = 10
    PROVEEDORES = 11
    # 12 — libre
    HARDWARE = 13
    VENTAS_DIGITALES = 14
    CARTELERIA_CONFIG = 15
    # 16 — libre
    CLIENTES = 17
    NEXUS = 18
    JEFE_DASHBOARD = 19
    JEFE_REPORTES = 20
    CARTELERIA = 21
    CARTELERIA_DASHBOARD = 22
    IA_BOSS = 23
    PROMEDIOS = 24
    AUDITORIA = 25
    PROVEEDORES_JEFE = 26
    PROVEEDORES_CARTELERIA = 27

    FREE = (12, 16)

    @classmethod
    def home_for_role(cls, role: str) -> int:
        role = (role or "admin").lower()
        if role == "cajero":
            return cls.CAJERO
        if role == "jefe":
            return cls.JEFE_DASHBOARD
        if role == "carteleria":
            return cls.CARTELERIA_DASHBOARD
        return cls.ADMIN_DASHBOARD
