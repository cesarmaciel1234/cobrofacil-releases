import os
import subprocess
import sqlite3
import tempfile
import sys
import shutil
import glob

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_de_datos.database import DatabaseManager

DB_PATH = ""
if len(sys.argv) > 1:
    DB_PATH = sys.argv[1]

ISQL_PATH = None
if len(sys.argv) > 2:
    ISQL_PATH = sys.argv[2] or None

def find_isql_path():
    firebird_root = os.environ.get("FIREBIRD")
    candidates = []
    if firebird_root:
        candidates.extend([
            os.path.join(firebird_root, "bin", "isql.exe"),
            os.path.join(firebird_root, "isql.exe"),
        ])
    candidates.extend([
        r"C:\Program Files (x86)\AbarrotesPDV\isql.exe",
        r"C:\Program Files\AbarrotesPDV\isql.exe",
        r"C:\AbarrotesPDV\isql.exe",
        r"C:\Program Files\Firebird\bin\isql.exe",
        r"C:\Program Files (x86)\Firebird\bin\isql.exe",
        r"C:\Program Files\Firebird\Firebird_3_0\bin\isql.exe",
        r"C:\Program Files\Firebird\Firebird_4_0\bin\isql.exe",
        r"C:\Program Files\Firebird\Firebird_5_0\bin\isql.exe",
        r"C:\Program Files (x86)\Firebird\Firebird_3_0\bin\isql.exe",
        r"C:\Program Files (x86)\Firebird\Firebird_4_0\bin\isql.exe",
        r"C:\Program Files (x86)\Firebird\Firebird_5_0\bin\isql.exe",
    ])
    for path in candidates:
        if os.path.exists(path):
            return path

    if DB_PATH:
        db_dir = os.path.dirname(DB_PATH)
        if os.path.isdir(db_dir):
            for path in [
                os.path.join(db_dir, "isql.exe"),
                os.path.join(db_dir, "..", "isql.exe"),
                os.path.join(db_dir, "bin", "isql.exe"),
            ]:
                path = os.path.normpath(path)
                if os.path.exists(path):
                    return path

    for path in (shutil.which("isql.exe"), shutil.which("isql")):
        if path and os.path.exists(path):
            return path

    for base in [r"C:\Program Files\Firebird", r"C:\Program Files (x86)\Firebird", r"C:\AbarrotesPDV"]:
        if os.path.isdir(base):
            for path in glob.glob(os.path.join(base, "**", "isql.exe"), recursive=True):
                if os.path.exists(path):
                    return path

    return None

ISQL_PATH = find_isql_path()

def ejecutar_isql(sql_query):
    """Ejecuta una consulta SQL en Firebird y devuelve el output como texto."""
    fd, temp_sql = tempfile.mkstemp(suffix=".sql")
    os.close(fd)
    
    with open(temp_sql, "w", encoding="utf-8") as f:
        f.write("SET LIST ON;\n" + sql_query)
        
    try:
        result = subprocess.run(
            [ISQL_PATH, "-u", "SYSDBA", "-p", "masterkey", DB_PATH, "-i", temp_sql],
            capture_output=True, text=True, encoding='latin1', errors='replace'
        )
        return result.stdout
    finally:
        if os.path.exists(temp_sql):
            os.remove(temp_sql)

def parsear_list_output(output):
    """Convierte el formato SET LIST ON de isql en una lista de diccionarios."""
    registros = []
    registro_actual = {}
    
    for line in output.splitlines():
        line = line.strip()
        if not line:
            if registro_actual:
                registros.append(registro_actual)
                registro_actual = {}
            continue
            
        if "  " in line:
            # Dividir por el primer espacio múltiple
            parts = [p for p in line.split("  ") if p]
            if len(parts) >= 2:
                key = parts[0].strip()
                val = parts[-1].strip()
                registro_actual[key] = val
    
    if registro_actual:
        registros.append(registro_actual)
        
    return registros

def importar_productos(db):
    print("Extrayendo PRODUCTOS de Eleventa...")
    query = "SELECT CODIGO, DESCRIPCION, PCOSTO, PVENTA, DINVENTARIO, TVENTA, IMPUESTOS FROM PRODUCTOS;"
    raw_data = ejecutar_isql(query)
    productos = parsear_list_output(raw_data)
    print(f"Encontrados {len(productos)} productos.")
    
    insertados = 0
    actualizados = 0
    for p in productos:
        codigo = p.get("CODIGO", "")
        nombre = p.get("DESCRIPCION", "")
        if not codigo or not nombre: continue
        
        def safe_float(val):
            if val == "<null>" or not val: return 0.0
            try: return float(val)
            except: return 0.0
            
        costo = safe_float(p.get("PCOSTO", 0))
        precio = safe_float(p.get("PVENTA", 0))
        stock = safe_float(p.get("DINVENTARIO", 0))
        tventa = p.get("TVENTA", "U") # G = Granel, U = Unidad
        es_pesable = 1 if tventa == "G" else 0
        unidad = "KG" if es_pesable else "UN"
        
        # Comprobar si existe
        existe = db.execute_scalar("SELECT id FROM productos WHERE codigo = ?", (codigo,))
        if existe:
            db.execute_non_query(
                "UPDATE productos SET nombre=?, costo=?, precio=?, stock=?, es_pesable=?, unidad=? WHERE codigo=?",
                (nombre, costo, precio, stock, es_pesable, unidad, codigo)
            )
            actualizados += 1
        else:
            db.execute_non_query(
                "INSERT INTO productos (codigo, nombre, costo, precio, stock, es_pesable, unidad) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (codigo, nombre, costo, precio, stock, es_pesable, unidad)
            )
            insertados += 1
            
    print(f"Productos: {insertados} Nuevos | {actualizados} Actualizados.")

def importar_clientes(db):
    print("Extrayendo CLIENTES de Eleventa...")
    query = "SELECT NUMERO, NOMBRE, TELEFONO, LIMITE_CREDITO, DSALDOACTUAL FROM CLIENTES;"
    raw_data = ejecutar_isql(query)
    clientes_raw = parsear_list_output(raw_data)
    print(f"[DEBUG] Total registros crudos de CLIENTES: {len(clientes_raw)}")
    
    if clientes_raw:
        print(f"[DEBUG] Primer cliente crudo: {clientes_raw[0]}")
    
    # Limpiar y filtrar clientes: remover nulls, espacios en blanco, y clientes "mostrador"
    clientes = []
    for c in clientes_raw:
        nombre = (c.get("NOMBRE", "") or "").strip()
        if not nombre or nombre.lower() in ("<null>", "null", "", "cliente general", "cliente mostrador", "mostrador"):
            continue
        clientes.append(c)
    
    print(f"Encontrados {len(clientes)} clientes válidos (filtrados de {len(clientes_raw)}).")
    
    insertados = 0
    actualizados = 0
    for c in clientes:
        def safe_float(val):
            if val == "<null>" or not val: return 0.0
            try: return float(val)
            except: return 0.0

        nombre = (c.get("NOMBRE", "") or "").strip()
        telefono = (c.get("TELEFONO", "") or "").strip()
        if telefono.lower() in ("<null>", "null"): telefono = ""
        limite = safe_float(c.get("LIMITE_CREDITO"))
        deuda = safe_float(c.get("DSALDOACTUAL"))
        
        if not nombre:
            continue
            
        # Buscar por nombre (Eleventa no obliga nombre único, pero nosotros sí intentamos no duplicar)
        existe = db.execute_scalar("SELECT id FROM clientes WHERE LOWER(nombre) = LOWER(?)", (nombre,))
        if existe:
            db.execute_non_query(
                "UPDATE clientes SET telefono=?, limite_credito=?, deuda_actual=? WHERE id=?",
                (telefono, limite, deuda, existe)
            )
            actualizados += 1
        else:
            db.execute_non_query(
                "INSERT INTO clientes (nombre, telefono, limite_credito, deuda_actual) VALUES (?, ?, ?, ?)",
                (nombre, telefono, limite, deuda)
            )
            insertados += 1

    print(f"Clientes: {insertados} Nuevos | {actualizados} Actualizados.")

def normalizar_fecha_eleventa(raw_str):
    import datetime
    raw_str = raw_str.strip().split(".")[0]  # Remover ms si hay
    if not raw_str or raw_str.upper() == "NULL" or raw_str == "<null>":
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Intentar varios formatos comunes
    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]
    
    # Mapear meses en español/inglés
    meses_map = {
        'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04', 'MAY': '05', 'JUN': '06',
        'JUL': '07', 'AGO': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12',
        'JAN': '01', 'APR': '04', 'AUG': '08', 'DEC': '12',
    }
    
    parts = raw_str.replace("-", " ").replace("/", " ").split()
    if len(parts) >= 3:
        mes_val = parts[1].upper()
        if mes_val in meses_map:
            parts[1] = meses_map[mes_val]
            raw_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
            if len(parts) >= 4:
                raw_str += f" {parts[3]}"
    
    for fmt in formatos:
        try:
            dt = datetime.datetime.strptime(raw_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
            
    # Parseo manual rústico
    try:
        clean = raw_str.replace("/", "-").replace("\\", "-")
        if " " in clean:
            f_part, h_part = clean.split(" ", 1)
        else:
            f_part, h_part = clean, "00:00:00"
            
        f_parts = f_part.split("-")
        if len(f_parts) == 3:
            if len(f_parts[2]) == 4:
                d, m, y = f_parts[0], f_parts[1], f_parts[2]
            elif len(f_parts[0]) == 4:
                y, m, d = f_parts[0], f_parts[1], f_parts[2]
            else:
                y, m, d = datetime.datetime.now().year, f_parts[1], f_parts[0]
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d} {h_part}"
    except:
        pass

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def importar_historial(db):
    print("Extrayendo HISTORIAL DE VENTAS de Eleventa...")
    # Primero, obtener info de VENTATICKETS sin filtro para diagnosticar
    query_info = "SELECT COUNT(*) AS TOTAL FROM VENTATICKETS;"
    raw_info = ejecutar_isql(query_info)
    info = parsear_list_output(raw_info)
    total_registros = int(info[0].get("TOTAL", "0") if info else 0) if info else 0
    print(f"[DEBUG] Total de registros en VENTATICKETS: {total_registros}")
    
    # Intentar consulta con varios filtros alternativos
    query = "SELECT ID, VENDIDO_EN, TOTAL, PAGO_CON, FORMA_PAGO FROM VENTATICKETS WHERE ESTA_ABIERTO = 'f' AND ESTA_CANCELADO = 'f';"
    raw_tickets = ejecutar_isql(query)
    tickets = parsear_list_output(raw_tickets)
    print(f"[DEBUG] Tickets con filtro f: {len(tickets)}")
    
    # Si no hay resultados, intentar con FALSE
    if not tickets:
        query_alt = "SELECT ID, VENDIDO_EN, TOTAL, PAGO_CON, FORMA_PAGO FROM VENTATICKETS WHERE ESTA_ABIERTO = FALSE AND ESTA_CANCELADO = FALSE;"
        raw_tickets = ejecutar_isql(query_alt)
        tickets = parsear_list_output(raw_tickets)
        print(f"[DEBUG] Tickets con filtro FALSE: {len(tickets)}")
    
    # Si aun no hay resultados, intentar sin filtro
    if not tickets and total_registros > 0:
        query_todos = "SELECT ID, VENDIDO_EN, TOTAL, PAGO_CON, FORMA_PAGO FROM VENTATICKETS;"
        raw_tickets = ejecutar_isql(query_todos)
        tickets = parsear_list_output(raw_tickets)
        print(f"[DEBUG] Tickets SIN FILTRO: {len(tickets)}")
        if tickets:
            print(f"[DEBUG] Primer ticket: {tickets[0]}")
    
    print(f"Encontrados {len(tickets)} tickets validos.")

    query_detalles = "SELECT TICKET_ID, PRODUCTO_CODIGO, PRODUCTO_NOMBRE, CANTIDAD, PRECIO_FINAL, TOTAL_ARTICULO FROM VENTATICKETS_ARTICULOS;"
    raw_detalles = ejecutar_isql(query_detalles)
    detalles = parsear_list_output(raw_detalles)
    print(f"Encontrados {len(detalles)} productos vendidos en la historia.")

    def safe_float(val):
        if val == "<null>" or not val: return 0.0
        try: return float(val)
        except: return 0.0

    print("Inyectando ventas en TPV Pro...")
    conn = db.get_connection()
    cursor = conn.cursor()
    if getattr(db, 'db_engine_type', 'sqlite') == 'mariadb':
        cursor.execute("START TRANSACTION;")
    else:
        cursor.execute("BEGIN TRANSACTION;")
    try:
        insertados_tickets = 0
        insertados_detalles = 0
        
        # Agrupar detalles por ticket para inyección más rápida
        det_por_ticket = {}
        for d in detalles:
            tid = d.get("TICKET_ID", "")
            if tid not in det_por_ticket: det_por_ticket[tid] = []
            det_por_ticket[tid].append(d)

        for t in tickets:
            tid = t.get("ID", "")
            fecha = normalizar_fecha_eleventa(t.get("VENDIDO_EN", ""))
            total = safe_float(t.get("TOTAL", 0))
            pago_con = safe_float(t.get("PAGO_CON", 0))
            forma_pago = t.get("FORMA_PAGO", "").strip() or "Efectivo"
            if forma_pago == "<null>": forma_pago = "Efectivo"
            if "CREDITO" in forma_pago.upper(): forma_pago = "Fiado"
            
            pago_efectivo = pago_con if forma_pago == "Efectivo" else 0
            pago_otro = total if forma_pago != "Efectivo" else 0

            # Insertar Venta
            cursor.execute('''
                INSERT INTO ventas (total, pago_con, pago_efectivo, pago_otro, cambio, estado, metodo_pago, usuario, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (total, pago_con, pago_efectivo, pago_otro, max(0, pago_con - total), 'COMPLETADA', forma_pago, 'Admin', fecha))
            nueva_venta_id = cursor.lastrowid
            insertados_tickets += 1

            # Insertar Detalles
            if tid in det_por_ticket:
                for d in det_por_ticket[tid]:
                    cod = d.get("PRODUCTO_CODIGO", "")
                    if cod == "<null>": cod = ""
                    nom = d.get("PRODUCTO_NOMBRE", "")
                    cant = safe_float(d.get("CANTIDAD", 0))
                    precio = safe_float(d.get("PRECIO_FINAL", 0))
                    tot = safe_float(d.get("TOTAL_ARTICULO", 0))
                    cursor.execute('''
                        INSERT INTO detalles_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (nueva_venta_id, cod, cant, precio, tot))
                    insertados_detalles += 1

        conn.commit()
        print(f"Tickets migrados: {insertados_tickets} | Artículos migrados: {insertados_detalles}")
    except Exception as e:
        conn.rollback()
        print(f"Error migrando historial: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("INICIANDO MIGRACION DESDE ELEVENTA A TPV PRO 2026")
    print("=" * 60)

    try:
        db = DatabaseManager()
    except Exception as e:
        import traceback
        print(f"Error inicializando DatabaseManager: {e}")
        traceback.print_exc()
        sys.exit(1)

    if not ISQL_PATH or not os.path.exists(ISQL_PATH):
        print("ERROR: No se encontró AbarrotesPDV / Firebird (isql.exe) en las rutas esperadas.")
        print(f"Ruta isql detectada: {ISQL_PATH or '<ninguna>'}")
        print("Buscar el ejecutable en:")
        print("  - C:\\Program Files (x86)\\AbarrotesPDV\\isql.exe")
        print("  - C:\\Program Files\\AbarrotesPDV\\isql.exe")
        print("  - C:\\AbarrotesPDV\\isql.exe")
        print("  - C:\\Program Files\\Firebird\\<version>\\bin\\isql.exe")
        print("También puede estar en el PATH si el instalador de Firebird lo agregó.")
        print(f"Ruta de base de datos usada: {DB_PATH}")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print("ERROR: No se encontró la base de datos PDVDATA.FDB.")
        print(f"Ruta de base de datos usada: {DB_PATH}")
        sys.exit(1)
        
    try:
        importar_productos(db)
        print("-" * 60)
        importar_clientes(db)
        print("-" * 60)
        importar_historial(db)
        print("=" * 60)
        print("MIGRACION COMPLETADA CON EXITO.")
    except Exception as e:
        import traceback
        print(f"Ocurrio un error inesperado: {e}")
        traceback.print_exc()
