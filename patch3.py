import re

with open('src/cerebro_global/proveedor/motor_proveedor.py', 'r', encoding='utf-8') as f:
    content = f.read()

def repl1(m):
    return '''    def get_proveedores_unicos(perfil, db_jefe=None):
        nombres = set()
        db, _modo = MotorProveedor._get_read_db(perfil, db_jefe)
        if not db: return []

        try:
            res_r = db.execute_query("SELECT DISTINCT proveedor FROM romaneos")
            if res_r:
                for r in res_r:
                    nombres.add(r['proveedor'] if isinstance(r, dict) else r[0])

            res_g = db.execute_query("SELECT descripcion FROM gastos WHERE categoria LIKE 'Mercader%'")
            if res_g:
                for r in res_g:
                    desc = r['descripcion'] if isinstance(r, dict) else r[0]
                    prov_match = re.search(r"Proveedor:\\s*(.*)", str(desc))
                    if prov_match:
                        nombres.add(prov_match.group(1).split('\\n')[0].strip())
        except Exception: pass

        return sorted(list(nombres))

    @staticmethod
    def load_proveedores'''

content = re.sub(
    r'    def get_proveedores_unicos\(perfil, db_jefe=None\):.*?    @staticmethod\n    def load_proveedores',
    repl1,
    content,
    flags=re.DOTALL
)

def repl2(m):
    return '''    def load_proveedores(perfil, db_jefe=None):
        db, _modo = MotorProveedor._get_read_db(perfil, db_jefe)
        if not db: return []
        parsed_rows = []
        try:
            res = db.execute_query("SELECT id, fecha, descripcion, monto, status FROM gastos WHERE categoria LIKE 'Mercader%' ORDER BY fecha DESC LIMIT 50")
            for r in (res or []):
                gid = str(r["id"] if isinstance(r, dict) else r[0])
                fecha = str(r["fecha"] if isinstance(r, dict) else r[1])
                desc_full = str(r["descripcion"] if isinstance(r, dict) else r[2])
                monto = float(r["monto"] if isinstance(r, dict) else r[3])
                status = str(r["status"] if isinstance(r, dict) else (r[4] if len(r) > 4 else "Pagado"))
                
                prov_match = re.search(r"Proveedor:\\s*(.*)", desc_full)
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
            print(f"Error load_proveedores (global): {e}")
        return parsed_rows

    @staticmethod
    def pagar_proveedor'''

content = re.sub(
    r'    def load_proveedores\(perfil, db_jefe=None\):.*?    @staticmethod\n    def pagar_proveedor',
    repl2,
    content,
    flags=re.DOTALL
)

with open('src/cerebro_global/proveedor/motor_proveedor.py', 'w', encoding='utf-8') as f:
    f.write(content)

