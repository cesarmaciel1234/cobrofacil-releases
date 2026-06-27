"""Fábricas lazy-load de pantallas para MainWindow."""

from src.navigation.screen_indices import Screen

SCREEN_COUNT = 24
FREE_SCREEN_SLOTS = Screen.FREE


def build_screen_factories(main_window):
    """Retorna {índice: callable} que instancia cada pantalla bajo demanda."""
    mw = main_window
    _imp = __import__

    return {
        Screen.ADMIN_DASHBOARD: lambda: _imp(
            "src.admin.admin0_dashboard", fromlist=["Admin0Dashboard"]
        ).Admin0Dashboard(),
        Screen.INVENTARIO: lambda: _imp(
            "src.admin.admin1_inventario", fromlist=["Admin1Inventario"]
        ).Admin1Inventario(),
        Screen.OFERTAS: lambda: _imp(
            "src.admin.admin2_ofertas", fromlist=["Admin2Ofertas"]
        ).Admin2Ofertas(),
        Screen.REPORTES: lambda: _imp(
            "src.admin.admin3_reportes", fromlist=["Admin3Reportes"]
        ).Admin3Reportes(),
        Screen.CONFIGURACION: lambda: _imp(
            "src.admin.admin5_configuracion", fromlist=["Admin5Configuracion"]
        ).Admin5Configuracion(),
        Screen.RED_LAN: lambda: _imp(
            "src.admin.admin6_red_lan", fromlist=["Admin6RedLan"]
        ).Admin6RedLan(),
        Screen.CIERRE: lambda: _imp(
            "src.admin.admin7_cierre", fromlist=["Admin7Cierre"]
        ).Admin7Cierre(mw),
        Screen.ETIQUETAS: lambda: _imp(
            "src.admin.etiquetas.admin_etiquetas", fromlist=["AdminEtiquetas"]
        ).AdminEtiquetas(),
        Screen.CONTABILIDAD: lambda: _imp(
            "src.jefe.contabilidad.jefe_contabilidad", fromlist=["JefeContabilidad"]
        ).JefeContabilidad(),
        Screen.MERCADO_PAGO: lambda: _imp(
            "src.admin.admin10_mp", fromlist=["Admin10MP"]
        ).Admin10MP(),
        Screen.PROVEEDORES: lambda: _imp(
            "src.admin.admin11_proveedores", fromlist=["Admin11Proveedores"]
        ).Admin11Proveedores(),
        Screen.HARDWARE: lambda: _imp(
            "src.admin.admin13_hardware", fromlist=["Admin13Hardware"]
        ).Admin13Hardware(),
        Screen.VENTAS_DIGITALES: lambda: _imp(
            "src.admin.admin14_ventas_digitales", fromlist=["Admin14VentasDigitales"]
        ).Admin14VentasDigitales(),
        Screen.CLIENTES: lambda: _imp(
            "src.admin.admin_clientes", fromlist=["AdminClientes"]
        ).AdminClientes(),
        Screen.NEXUS: lambda: _imp(
            "src.admin.admin7_nexus", fromlist=["NexusExtremeControl"]
        ).NexusExtremeControl(),
        Screen.JEFE_DASHBOARD: lambda: _imp(
            "src.jefe.jefe0_dashboard", fromlist=["Jefe0Dashboard"]
        ).Jefe0Dashboard(),
        Screen.JEFE_REPORTES: lambda: _imp(
            "src.jefe.reportes.reportes_main", fromlist=["ReportesMain"]
        ).ReportesMain(),
        Screen.CARTELERIA: lambda: _imp(
            "src.carteleria.main_board", fromlist=["CarteleriaMain"]
        ).CarteleriaMain(),
        Screen.IA_BOSS: lambda: _imp(
            "src.admin.admin12_ai_boss", fromlist=["Admin12AIBoss"]
        ).Admin12AIBoss(),
    }
