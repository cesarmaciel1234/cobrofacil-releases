"""
Estado global del cajero en terminal: estación 1 (titular) o 2 (auxiliar).
Tras F8 + PIN define impresora y cajón físico para cobros y movimientos.
"""


class CajeroActivo:
    numero = 1
    nombre = "CAJERO"

    @classmethod
    def set(cls, numero):
        from src.config import config
        cls.numero = numero
        cls.nombre = config.get(
            f"nombre_cajero_{numero}",
            "CAJERO" if numero == 1 else "AUXILIAR",
        ).upper()

    @classmethod
    def printer_key(cls):
        return "ticket_printer_2" if cls.numero == 2 else "ticket_printer"

    @classmethod
    def get_printer_name(cls):
        from src.config import config as _c
        return _c.get(cls.printer_key(), "")

    @classmethod
    def get_drawer_target(cls):
        """Impresora o puerto COM del cajón del cajero activo."""
        from src.config import config as _c
        if cls.numero == 2:
            com = (_c.get("drawer_com_port_2") or "").strip()
            if com and "ninguno" not in com.lower():
                return com
        return cls.get_printer_name() or _c.get("ticket_printer", _c.get("printer_name", ""))
