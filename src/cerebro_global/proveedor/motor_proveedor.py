import re

class MotorProveedor:
    """
    Cerebro Global para la gestión de Proveedores.
    Contiene la lógica agnóstica de UI para interactuar con la Base de Datos.
    Soporta operaciones tanto para SQLite (Jefe) como MariaDB (Admin/Red).
    """
    
    @staticmethod
    def _get_db(perfil, db_jefe=None):
        if perfil == "jefe" and db_jefe:
            return db_jefe
        else:
            try:
                from src.base_de_datos.database import db_manager
                return db_manager
            except Exception:
                return None

    @staticmethod
    def get_proveedores_unicos(perfil, db_jefe=None):
        """Retorna una lista de nombres únicos de proveedores usados históricamente."""
        nombres = set()
        db = MotorProveedor._get_db(perfil, db_jefe)
        if not db: return []
        
        if perfil == "jefe" and db_jefe:
            try:
                rows = db.get_general_debts()
                rows = [r for r in (rows or []) if str(r[2] or "") == "Proveedor"]
                for row in rows:
                    desc_full = str(row[1] or "")
                    prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
                    if prov_match:
                        nombres.add(prov_match.group(1).split('\n')[0].strip())
            except Exception: pass
        else:
            try:
                # Intentar cargar desde romaneos si existe
                res_r = db.execute_query("SELECT DISTINCT proveedor FROM romaneos")
                if res_r:
                    for r in res_r:
                        nombres.add(r['proveedor'] if isinstance(r, dict) else r[0])
                
                # Y desde gastos por las dudas
                res_g = db.execute_query("SELECT descripcion FROM gastos WHERE categoria = 'Mercadería / Stock'")
                if res_g:
                    for r in res_g:
                        desc = r['descripcion'] if isinstance(r, dict) else r[0]
                        prov_match = re.search(r"Proveedor:\s*(.*)", str(desc))
                        if prov_match:
                            nombres.add(prov_match.group(1).split('\n')[0].strip())
            except Exception: pass
            
        return sorted(list(nombres))

    @staticmethod
    def load_proveedores(perfil, db_jefe=None):
        """Devuelve una lista de diccionarios unificada con el historial de compras."""
        db = MotorProveedor._get_db(perfil, db_jefe)
        if not db: return []
        
        parsed_rows = []
        if perfil == "jefe" and db_jefe:
            try:
                rows = db.get_general_debts()
                rows = [r for r in (rows or []) if str(r[2] or "") == "Proveedor"]
                for row in rows:
                    monto   = float(row[3] or 0)
                    pagado  = float(row[6] if len(row) > 6 else 0)
                    rest    = monto - pagado
                    status  = str(row[5] or "pending")
                    desc_full = str(row[1] or "")
                    
                    prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
                    prov_show = prov_match.group(1).strip() if prov_match else "Proveedor General"
                    
                    parsed_rows.append({
                        "id": row[0],
                        "proveedor": prov_show,
                        "monto": monto,
                        "pagado": pagado,
                        "restante": rest,
                        "fecha": str(row[4] or ""),
                        "estado": status,
                        "desc_full": desc_full
                    })
            except Exception as e:
                print(f"Error load_proveedores (jefe): {e}")
        else:
            try:
                res = db.execute_query("SELECT id, fecha, descripcion, monto, status FROM gastos WHERE categoria = 'Mercadería / Stock' ORDER BY fecha DESC LIMIT 50")
                for r in (res or []):
                    gid = str(r["id"] if isinstance(r, dict) else r[0])
                    fecha = str(r["fecha"] if isinstance(r, dict) else r[1])
                    desc_full = str(r["descripcion"] if isinstance(r, dict) else r[2])
                    monto = float(r["monto"] if isinstance(r, dict) else r[3])
                    status = str(r["status"] if isinstance(r, dict) else (r[4] if len(r) > 4 else "Pagado"))
                    
                    prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
                    prov_show = prov_match.group(1).strip() if prov_match else "Proveedor General"
                    
                    if status in ("Pendiente", "pending"):
                        rest = monto
                        pagado = 0.0
                    else:
                        rest = 0.0
                        pagado = monto
                        
                    parsed_rows.append({
                        "id": gid,
                        "proveedor": prov_show,
                        "monto": monto,
                        "pagado": pagado,
                        "restante": rest,
                        "fecha": fecha,
                        "estado": status,
                        "desc_full": desc_full
                    })
            except Exception as e:
                print(f"Error load_proveedores (admin): {e}")
                
        return parsed_rows

    @staticmethod
    def pagar_proveedor(debt_id, amt, perfil, db_jefe=None):
        """Registra un pago sobre una deuda existente."""
        if perfil == "jefe" and db_jefe:
            db_jefe.pay_debt(debt_id, amt)
        else:
            db = MotorProveedor._get_db(perfil, db_jefe)
            db.execute_non_query("UPDATE gastos SET status = 'Pagado' WHERE id = ?", (debt_id,))

    @staticmethod
    def save_proveedor(date, prov_name, tropa, grupos, payment, amount, perfil, db_jefe=None):
        """Registra una compra/romaneo. Retorna (True, desc) o (False, msg_error)."""
        # 1. Guardar detalle en Romaneos (MariaDB de red) si hay red
        try:
            from src.base_de_datos.database import db_manager
            from src.cerebro_global.desposte.motor_rendimiento import MotorRendimiento
            
            if db_manager and hasattr(db_manager, "execute_non_query"):
                for (merc, precio), items in grupos.items():
                    total_kilos = sum([p for n, p in items])
                    monto_grupo = total_kilos * precio
                    
                    db_manager.execute_non_query(
                        "INSERT INTO romaneos (fecha, proveedor, tropa, tipo_carne, precio_unitario, total_kilos, monto_total, estado_pago, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (date, prov_name, tropa, merc, precio, total_kilos, monto_grupo, payment, perfil)
                    )
                    res = db_manager.execute_query("SELECT id FROM romaneos ORDER BY id DESC LIMIT 1")
                    if res and len(res) > 0:
                        romaneo_id = res[0]['id'] if isinstance(res[0], dict) else res[0][0]
                        for nro, peso in items:
                            db_manager.execute_non_query(
                                "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                                (romaneo_id, nro, peso)
                            )
                            
                    # Desposte Automático: Inyectar proporción de kilos al inventario base usando db_manager
                    # (La base de jefe para leer el historial, y db_manager como admin para actualizar el stock)
                    if db_jefe:
                        MotorRendimiento.aplicar_desposte_a_stock(merc, total_kilos, db_manager, db_jefe)
        except Exception as e:
            print(f"Error DB central romaneos: {e}")
        
        # 2. Generar descripción estructurada
        desc = f"Proveedor: {prov_name}\nTropa: {tropa}\n\n--- DETALLE DE COMPRA ---\n"
        for (merc, precio), items in grupos.items():
            total_kilos = sum([p for n, p in items])
            monto_grupo = total_kilos * precio
            pesos_list = [f"{p:.2f}" for n, p in items]
            if len(pesos_list) > 20:
                pesos_str = ", ".join(pesos_list[:20]) + f" ... (y {len(pesos_list)-20} más)"
            else:
                pesos_str = ", ".join(pesos_list)
                
            desc += f"• {merc} ({len(items)} ítems):\n"
            desc += f"  ↳ Pesos: [{pesos_str}]\n"
            desc += f"  ↳ Total Kg/Cajas: {total_kilos:.2f} | Precio Unit: ${precio:,.2f} | Subtotal: ${monto_grupo:,.2f}\n\n"
        desc += f"TOTAL GENERAL: ${amount:,.2f}"

        # 3. Guardar registro contable según perfil
        try:
            if perfil == "jefe" and db_jefe:
                if payment == "Contado (Pago Inmediato)":
                    db_jefe.add_expense(date, "Mercadería / Stock", amount, desc, 'variable')
                else:
                    db_jefe.add_general_debt(desc, "Proveedor", amount, date)
            else:
                db = MotorProveedor._get_db(perfil, db_jefe)
                status_pag = "Pagado" if payment == "Contado (Pago Inmediato)" else "Pendiente"
                db.execute_non_query(
                    "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario) VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)",
                    (date, desc, amount, status_pag, perfil)
                )
            return True, desc
        except Exception as e:
            return False, str(e)
