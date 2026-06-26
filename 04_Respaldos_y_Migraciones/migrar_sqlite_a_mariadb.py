#!/usr/bin/env python3
"""
Migra datos de SQLite (AQVGI.db) a MariaDB (CobroFacil_POS)
Preserva clientes, ventas y detalles de ventas existentes.
"""

import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_de_datos.database import DatabaseManager

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "AQVGI.db")

def conectar_sqlite():
    """Conecta a la base de datos SQLite antigua."""
    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: No se encontró {SQLITE_PATH}")
        return None
    return sqlite3.connect(SQLITE_PATH)

def obtener_tablas_sqlite(conn):
    """Obtiene lista de tablas en SQLite."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def migrar_clientes(sqlite_conn, mariadb_conn):
    """Migra clientes de SQLite a MariaDB."""
    print("\n[*] Migrando CLIENTES de SQLite a MariaDB...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mariadb_cursor = mariadb_conn.get_connection().cursor()
    
    try:
        # Obtener clientes de SQLite
        sqlite_cursor.execute("""
            SELECT id, nombre, telefono, limite_credito, deuda_actual
            FROM clientes
        """)
        clientes = sqlite_cursor.fetchall()
        print(f"[DEBUG] Encontrados {len(clientes)} clientes en SQLite")
        
        insertados = 0
        actualizados = 0
        
        for cliente in clientes:
            cliente_id, nombre, telefono, limite_credito, deuda_actual = cliente
            
            if not nombre or not nombre.strip():
                continue
            
            # Normalizar valores None
            telefono = telefono or ""
            limite_credito = float(limite_credito or 0)
            deuda_actual = float(deuda_actual or 0)
            
            # Verificar si el cliente ya existe por nombre
            existe = mariadb_conn.execute_scalar(
                "SELECT id FROM clientes WHERE LOWER(nombre) = LOWER(%s)",
                (nombre,)
            )
            
            if existe:
                # Actualizar si es diferente
                mariadb_conn.execute_non_query(
                    """UPDATE clientes 
                       SET telefono=%s, limite_credito=%s, deuda_actual=%s 
                       WHERE id=%s""",
                    (telefono, limite_credito, deuda_actual, existe)
                )
                actualizados += 1
            else:
                # Insertar nuevo cliente
                mariadb_conn.execute_non_query(
                    """INSERT INTO clientes 
                       (nombre, telefono, limite_credito, deuda_actual)
                       VALUES (%s, %s, %s, %s)""",
                    (nombre, telefono, limite_credito, deuda_actual)
                )
                insertados += 1
        
        print(f"[OK] Clientes: {insertados} Nuevos | {actualizados} Actualizados")
        return insertados + actualizados
        
    except Exception as e:
        print(f"[ERROR] Migrando clientes: {e}")
        import traceback
        traceback.print_exc()
        return 0

def migrar_ventas(sqlite_conn, mariadb_conn):
    """Migra ventas y detalles de ventas de SQLite a MariaDB."""
    print("\n[*] Migrando VENTAS Y DETALLES de SQLite a MariaDB...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mariadb_conn_inst = mariadb_conn.get_connection()
    
    try:
        # Obtener ventas de SQLite
        sqlite_cursor.execute("""
            SELECT id, fecha, total, pago_con, cambio, pago_efectivo, pago_otro, 
                   usuario, estado, metodo_pago
            FROM ventas
        """)
        ventas = sqlite_cursor.fetchall()
        print(f"[DEBUG] Encontradas {len(ventas)} ventas en SQLite")
        
        insertados_ventas = 0
        insertados_detalles = 0
        
        for venta in ventas:
            venta_id, fecha, total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago = venta
            
            total = float(total or 0)
            pago_con = float(pago_con or 0)
            cambio = float(cambio or 0)
            pago_efectivo = float(pago_efectivo or 0)
            pago_otro = float(pago_otro or 0)
            metodo_pago = metodo_pago or "Efectivo"
            estado = estado or "COMPLETADA"
            usuario = usuario or "Admin"
            
            # Verificar si la venta ya existe (por fecha y total)
            existe = mariadb_conn.execute_scalar(
                "SELECT id FROM ventas WHERE fecha=%s AND total=%s LIMIT 1",
                (fecha, total)
            )
            
            if not existe:
                # Insertar venta
                mariadb_conn.execute_non_query(
                    """INSERT INTO ventas 
                       (fecha, total, pago_con, cambio, pago_efectivo, pago_otro, metodo_pago, estado, usuario)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (fecha, total, pago_con, cambio, pago_efectivo, pago_otro, metodo_pago, estado, usuario)
                )
                
                # Obtener el ID de la venta insertada (por fecha y total, que son únicos)
                nueva_venta_id = mariadb_conn.execute_scalar(
                    "SELECT id FROM ventas WHERE fecha=%s AND total=%s ORDER BY id DESC LIMIT 1",
                    (fecha, total)
                )
                insertados_ventas += 1
                
                # Obtener detalles de esta venta
                sqlite_cursor.execute(
                    "SELECT id_producto, nombre_producto, cantidad, precio_unitario, subtotal FROM detalles_ventas WHERE id_venta=?",
                    (venta_id,)
                )
                detalles = sqlite_cursor.fetchall()
                
                for detalle in detalles:
                    id_producto, nombre_producto, cantidad, precio_unitario, subtotal = detalle
                    cantidad = float(cantidad or 0)
                    precio_unitario = float(precio_unitario or 0)
                    subtotal = float(subtotal or 0)
                    
                    # Insertar detalle
                    mariadb_conn.execute_non_query(
                        """INSERT INTO detalles_ventas 
                           (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (nueva_venta_id, id_producto, cantidad, precio_unitario, subtotal)
                    )
                    insertados_detalles += 1
        
        print(f"[OK] Ventas: {insertados_ventas} | Detalles: {insertados_detalles}")
        return insertados_ventas + insertados_detalles
        
    except Exception as e:
        print(f"[ERROR] Migrando ventas: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACION DE SQLITE (AQVGI.db) A MARIADB")
    print("=" * 60)
    
    # Conectar a SQLite
    sqlite_conn = conectar_sqlite()
    if not sqlite_conn:
        sys.exit(1)
    
    print(f"\n[OK] Conectado a SQLite: {SQLITE_PATH}")
    
    # Listar tablas en SQLite
    tablas = obtener_tablas_sqlite(sqlite_conn)
    print(f"[*] Tablas en SQLite: {', '.join(tablas)}")
    
    # Conectar a MariaDB
    try:
        mariadb_conn = DatabaseManager()
        print("[OK] Conectado a MariaDB")
    except Exception as e:
        print(f"[ERROR] Conexión a MariaDB falló: {e}")
        sys.exit(1)
    
    # Desactivar foreign keys
    print("\n[*] Desactivando foreign key constraints...")
    mariadb_conn.execute_non_query("SET FOREIGN_KEY_CHECKS=0")
    
    # Limpiar tablas
    print("[*] Limpiando tablas...")
    try:
        mariadb_conn.execute_non_query("DELETE FROM detalles_ventas")
        mariadb_conn.execute_non_query("DELETE FROM ventas")
        mariadb_conn.execute_non_query("DELETE FROM clientes")
    except:
        pass
    
    # Ejecutar migraciones
    total_migrado = 0
    total_migrado += migrar_clientes(sqlite_conn, mariadb_conn)
    total_migrado += migrar_ventas(sqlite_conn, mariadb_conn)
    
    # Reactivar foreign keys
    print("\n[*] Reactivando foreign key constraints...")
    mariadb_conn.execute_non_query("SET FOREIGN_KEY_CHECKS=1")
    
    print("\n" + "=" * 60)
    print(f"MIGRACION COMPLETADA: {total_migrado} registros migrados")
    print("=" * 60)
    
    sqlite_conn.close()
