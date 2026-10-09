from src.config import config
from src.hardware.constructor_ticket.encabezado.generador import generar_encabezado
from src.hardware.constructor_ticket.cuerpo_productos.generador import generar_cuerpo
from src.hardware.constructor_ticket.totales_vuelto.generador import generar_totales
from src.hardware.constructor_ticket.pie_condiciones.generador import generar_pie

class ConstructorTicketVenta:
    @staticmethod
    def construir(
        empresa, cuit, direccion,
        num_venta, items, total, pago, cambio, estado,
        discount_amount, surcharge_amount,
        cajero, cajero_secundario,
        metodo_pago, cliente_nombre,
        saldo_anterior, saldo_disponible, abono_cuenta,
        mensaje_extra_condiciones,
        factura_electronica_data,
        abrir_cajon, config_drawer_pin, config_3nstar,
        calcular_iva_func
    ):
        ancho_mm = config.get("printer_paper_width_mm", 58)
        columnas = 48 if ancho_mm == 80 else 32

        data = bytearray()
        
        # 1. Encabezado
        data.extend(generar_encabezado(
            columnas, empresa, cuit, direccion, estado, num_venta, 
            cajero, cajero_secundario, factura_electronica_data
        ))
        
        # 2. Cuerpo
        data.extend(generar_cuerpo(columnas, items))
        
        # 3. Totales
        data.extend(generar_totales(
            columnas, total, pago, cambio, metodo_pago, items,
            discount_amount, surcharge_amount,
            factura_electronica_data, calcular_iva_func
        ))
        
        # 4. Pie y Condiciones (incluye corte de papel y cajon)
        data.extend(generar_pie(
            columnas, num_venta, total, cliente_nombre,
            saldo_anterior, saldo_disponible, abono_cuenta,
            mensaje_extra_condiciones, factura_electronica_data,
            abrir_cajon, config_drawer_pin, config_3nstar
        ))
        
        return data
