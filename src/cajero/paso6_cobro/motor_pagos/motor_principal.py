from typing import Dict, Any, Tuple, Optional
from src.cajero.paso6_cobro.motor_pagos.dtos.orden_cobro import OrdenCobroDTO
from src.cajero.paso6_cobro.motor_pagos.procesos.base_proceso import BaseProcesoPago

class MotorPrincipalCobros:
    """
    El orquestador central del Paso 6.
    Recibe la orden de la interfaz gráfica y la lanza hacia el Subproceso Independiente correspondiente.
    """
    
    @classmethod
    def iniciar_transaccion(cls, metodo: str, datos_ui: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Punto de entrada único. La UI solo debe llamar a este método.
        """
        # Convertir datos brutos de la UI a un DTO puro
        orden = OrdenCobroDTO(
            total_final=datos_ui.get("total_final", 0.0),
            items_carrito=datos_ui.get("items_carrito", []),
            cajero_actual=datos_ui.get("cajero", ""),
            cajero_secundario=datos_ui.get("cajero_sec", ""),
            monto_descuento=datos_ui.get("descuento", 0.0),
            monto_recargo=datos_ui.get("recargo", 0.0),
            descuentaso_oferta=datos_ui.get("oferta", 0.0),
            imprimir_ticket=datos_ui.get("imprimir", True),
            forzar_fiscal=datos_ui.get("force_fiscal", False)
        )
        
        # Opcional: Pasar parámetros extra legacy por ahora hasta la migración total
        orden.legacy_p1 = datos_ui.get("p1")
        orden.legacy_p2 = datos_ui.get("p2")
        orden.legacy_nombre_pendiente = datos_ui.get("nombre_pendiente")
        orden.legacy_cliente_id = datos_ui.get("cliente_id")

        metodo_limpio = metodo.lower().strip()
        proceso: Optional[BaseProcesoPago] = None
        
        if metodo_limpio == "efectivo":
            # from src.cajero.paso6_cobro.motor_pagos.procesos.proceso_efectivo.efectivo_main import ProcesoEfectivo
            # proceso = ProcesoEfectivo(orden)
            pass
        elif metodo_limpio in ("tarjeta", "crédito", "débito"):
            pass
        
        if proceso:
            return proceso.ejecutar()
            
        # Fallback al viejo controlador si el método aún no ha sido migrado al nuevo subproceso
        return cls._fallback_legacy(metodo, datos_ui)
        
    @classmethod
    def _fallback_legacy(cls, metodo: str, datos_ui: Dict[str, Any]) -> Tuple[bool, str]:
        from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import CobroController
        exito, msg = CobroController.completar_transaccion(
            total_final=datos_ui.get("total_final", 0.0),
            metodo=metodo,
            p1=datos_ui.get("p1"),
            p2=datos_ui.get("p2"),
            items_carrito=datos_ui.get("items_carrito", []),
            cajero=datos_ui.get("cajero", ""),
            cajero_sec=datos_ui.get("cajero_sec", ""),
            descuento=datos_ui.get("descuento", 0.0),
            recargo=datos_ui.get("recargo", 0.0),
            oferta=datos_ui.get("oferta", 0.0),
            nombre_pendiente=datos_ui.get("nombre_pendiente"),
            cliente_id=datos_ui.get("cliente_id"),
            imprimir=datos_ui.get("imprimir", True),
            force_fiscal=datos_ui.get("force_fiscal", False),
            request_id=datos_ui.get("request_id")
        )
        return exito, msg or "Transacción delegada al motor Legacy."
