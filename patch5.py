# -*- coding: utf-8 -*-
import re

with open('src/cerebro_global/proveedor/motor_proveedor.py', 'r', encoding='utf-8') as f:
    content = f.read()

def repl3(m):
    return '''    def pagar_proveedor(debt_id, amt, perfil, db_jefe=None):
        if not MotorProveedor.tienda_disponible():
            raise RuntimeError("Los pagos a proveedores requieren conexion con la tienda.")
        from src.base_de_datos.database import db_manager

        conn = MotorProveedor._abrir_conexion_tienda(db_manager)
        try:
            tienda = _ConexionTienda(db_manager, conn)
            if not tienda.execute_non_query(
                "UPDATE gastos SET status = 'Pagado' WHERE id = ?", (debt_id,)
            ):
                raise RuntimeError("No se encontro la deuda del proveedor para registrar el pago.")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def save_proveedor'''

content = re.sub(
    r'    def pagar_proveedor\(debt_id, amt, perfil, db_jefe=None\):.*?    @staticmethod\n    def save_proveedor',
    repl3,
    content,
    flags=re.DOTALL
)

def repl4(m):
    return '''            desc += f"TOTAL GENERAL: "
            status_pag = "Pagado" if payment == "Contado (Pago Inmediato)" else "Pendiente"
            if not tienda.execute_non_query(
                "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario) VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)",
                (date, desc, amount, status_pag, perfil)
            ):
                raise RuntimeError("No se pudo guardar la deuda del proveedor.")
            conn.commit()
            return True, desc
        except Exception as e:'''

content = re.sub(
    r'            desc \+= f"TOTAL GENERAL: \$\{amount:,\.2f\}".*?        except Exception as e:',
    repl4,
    content,
    flags=re.DOTALL
)

with open('src/cerebro_global/proveedor/motor_proveedor.py', 'w', encoding='utf-8') as f:
    f.write(content)
