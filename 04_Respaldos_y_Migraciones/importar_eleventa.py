import os
import subprocess
import sqlite3
import tempfile
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_de_datos.database import DatabaseManager

DB_PATH = r"C:\Program Files (x86)\AbarrotesPDV\db\PDVDATA.FDB"
if len(sys.argv) > 1:
    DB_PATH = sys.argv[1]

ISQL_PATH = r"C:\Program Files (x86)\AbarrotesPDV\isql.exe"
if not os.path.exists(ISQL_PATH):
    # Intentar buscar en Program Files normal
    ISQL_PATH = r"C:\Program Files\AbarrotesPDV\isql.exe"

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
    clientes = parsear_list_output(raw_data)
    
    # Filtrar cliente 0 o cliente mostrador genérico si existe
    clientes = [c for c in clientes if c.get("NOMBRE") and c.get("NOMBRE") != "NULL" and c.get("NOMBRE").lower() != "cliente general"]
    print(f"Encontrados {len(clientes)} clientes válidos.")
    
    insertados = 0
    actualizados = 0
    for c in clientes:
        def safe_float(val):
            if val == "<null>" or not val: return 0.0
            try: return float(val)
            except: return 0.0

        nombre = c.get("NOMBRE", "")
        telefono = c.get("TELEFONO", "")
        if telefono == "NULL" or telefono == "<null>": telefono = ""
        limite = safe_float(c.get("LIMITE_CREDITO", 0))
        deuda = safe_float(c.get("DSALDOACTUAL", 0))
        
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

def importar_historial(db):
    print("Extrayendo HISTORIAL DE VENTAS de Eleventa...")
    query = "SELECT ID, VENDIDO_EN, TOTAL, PAGO_CON, FORMA_PAGO FROM VENTATICKETS WHERE ESTA_ABIERTO = 'f' AND ESTA_CANCELADO = 'f';"
    raw_tickets = ejecutar_isql(query)
    tickets = parsear_list_output(raw_tickets)
    print(f"Encontrados {len(tickets)} tickets válidos.")

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
            fecha = t.get("VENDIDO_EN", "").split(".")[0] # remover ms si hay
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
    db = DatabaseManager()
    
    if not os.path.exists(ISQL_PATH):
        print("❌ Error: No se encontró AbarrotesPDV (isql.exe) en la ruta esperada.")
        sys.exit(1)
        
    if not os.path.exists(DB_PATH):
        print("❌ Error: No se encontró la base de datos PDVDATA.FDB.")
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
        print(f"Ocurrio un error inesperado: {e}")
