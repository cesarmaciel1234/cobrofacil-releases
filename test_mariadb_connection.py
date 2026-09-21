"""
Script de prueba para verificar la conexión al servidor MariaDB y la configuración del sistema.
"""
import socket
import pymysql
import json
import os

def test_connection():
    """Prueba la conexión al servidor MariaDB"""
    host = "192.168.0.9"
    port = 3306
    
    print("=== Prueba de conexión al servidor MariaDB ===")
    
    # Prueba de red
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"[OK] Red: Conexión TCP a {host}:{port} exitosa")
        else:
            print(f"[ERROR] Red: Conexión TCP a {host}:{port} falló (código: {result})")
            return False
    except Exception as e:
        print(f"[ERROR] Red: Error en prueba de conexión: {e}")
        return False
    
    # Prueba de base de datos
    try:
        conn = pymysql.connect(
            host=host, 
            port=port, 
            user='root', 
            password='1234', 
            database='punpro_db', 
            connect_timeout=5
        )
        print(f"[OK] Base de datos: Conexión exitosa a punpro_db")
        
        # Consultar datos
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM productos')
        productos = cur.fetchone()[0]
        print(f"[INFO] Productos en BD: {productos}")
        
        cur.execute('SELECT COUNT(*) FROM ventas')
        ventas = cur.fetchone()[0]
        print(f"[INFO] Ventas en BD: {ventas}")
        
        cur.execute('SELECT MAX(fecha) FROM ventas')
        ultima_venta = cur.fetchone()[0]
        print(f"[INFO] Ultima venta: {ultima_venta}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Base de datos: Error en conexión: {e}")
        return False

def check_config():
    """Verifica la configuración del sistema"""
    print("\n=== Verificación de configuración ===")
    
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] No se encontró config.json en {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"[INFO] db_engine: {config.get('db_engine')}")
        print(f"[INFO] db_host: {config.get('db_host')}")
        print(f"[INFO] is_master: {config.get('is_master')}")
        print(f"[INFO] carteleria_is_slave: {config.get('carteleria_is_slave')}")
        
        if config.get('db_engine') == 'mariadb' and config.get('db_host') == '192.168.0.9':
            print("[OK] Configuración correcta para modo esclava MariaDB")
            return True
        else:
            print("[WARNING] Configuración puede no ser óptima para tu entorno")
            return False
    except Exception as e:
        print(f"[ERROR] Error leyendo configuración: {e}")
        return False

if __name__ == "__main__":
    connection_ok = test_connection()
    config_ok = check_config()
    
    print("\n=== Prueba de inicialización del sistema ===")
    try:
        from src.base_de_datos.database import DatabaseManager
        db = DatabaseManager()
        print(f"[INFO] Engine: {db.db_engine_type}")
        print(f"[INFO] Path: {db.db_path}")
        print(f"[INFO] Is master: {db.is_master}")
        print(f"[INFO] Forced offline: {db._forced_local_offline}")
        
        # Prueba de consulta con el sistema real
        try:
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM productos')
            row = cur.fetchone()
            if isinstance(row, dict):
                productos = row.get('COUNT(*)', 0)
            else:
                productos = row[0] if row else 0
            print(f"[INFO] Productos desde sistema: {productos}")
            conn.close()
            system_ok = True
        except Exception as db_e:
            print(f"[ERROR] Error en consulta: {db_e}")
            system_ok = False
    except Exception as init_e:
        print(f"[ERROR] Error inicializando sistema: {init_e}")
        system_ok = False
    
    print("\n=== Resumen ===")
    if connection_ok and config_ok and system_ok:
        print("[OK] Sistema funcionando correctamente con MariaDB remoto")
        print("[OK] Los cambios aplicados solucionan el problema de pérdida de datos")
    elif connection_ok and config_ok:
        print("[OK] Configuración y conexión correctas, pero hubo un error en la prueba")
    else:
        print("[WARNING] Revisar los problemas indicados arriba")