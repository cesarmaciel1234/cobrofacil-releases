from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class OrdenCobroDTO:
    """
    Data Transfer Object puro.
    Contiene ÚNICAMENTE la información universal de la compra.
    No contiene datos específicos de método (ni cliente_id, ni token_mercadopago, etc.)
    Esos datos los gestiona internamente el subproceso correspondiente.
    """
    total_final: float
    items_carrito: List[Dict[str, Any]]
    cajero_actual: str
    cajero_secundario: str
    monto_descuento: float = 0.0
    monto_recargo: float = 0.0
    descuentaso_oferta: float = 0.0
    imprimir_ticket: bool = True
    forzar_fiscal: bool = False
