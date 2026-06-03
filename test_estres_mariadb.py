import threading
import time
import sys
import random
from src.db_engines.mariadb_engine import MariaDBEngine
from src.services.mariadb_controller import mariadb_controller

# Configuracion del test
CAJEROS_SIMULTANEOS = 10
VENTAS_POR_CAJERO = 500

print("==================================================")
print("   PRUEBA DE ESTRES MARIADB - MULTIPLES CAJAS")
print("==================================================")
print(f"Simulando {CAJEROS_SIMULTANEOS} cajas cobrando al mismo tiempo.")
print(f"Cada caja realizará {VENTAS_POR_CAJERO} ventas (Total: {CAJEROS_SIMULTANEOS * VENTAS_POR_CAJERO} transacciones).")
print("==================================================\n")

# 1. Asegurarnos de que el servidor este corriendo
print("[*] Levantando servidor MariaDB...")
if not mariadb_controller.start_server():
    print("[!] Error fatal: No se pudo arrancar MariaDB.")
    sys.exit(1)

time.sleep(2) # Dar tiempo a que acepte conexiones

# 2. Crear tabla de prueba
engine = MariaDBEngine()
try:
    print("[*] Creando tabla temporal de pruebas...")
    conn = engine.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas_stress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            caja_id INT,
            monto DECIMAL(10,2),
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("TRUNCATE TABLE ventas_stress")
    conn.commit()
except Exception as e:
    print(f"[!] Error creando tabla: {e}")
    sys.exit(1)

# Variables de control
errores = 0
exitos = 0
lock = threading.Lock()

def tarea_cajero(caja_id):
    global errores, exitos
    
    # Cada hilo obtiene su propia conexion a traves del engine (thread-local)
    thread_engine = MariaDBEngine()
    
    for i in range(VENTAS_POR_CAJERO):
        monto = round(random.uniform(10.0, 5000.0), 2)
        query = "INSERT INTO ventas_stress (caja_id, monto) VALUES (?, ?)"
        
        try:
            conn = thread_engine.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (caja_id, monto))
            conn.commit()
            exito = True
        except Exception:
            exito = False
        
        with lock:
            if exito:
                exitos += 1
            else:
                errores += 1

print("\n[*] Iniciando bombardeo de transacciones...")
inicio = time.time()

hilos = []
for caja in range(1, CAJEROS_SIMULTANEOS + 1):
    h = threading.Thread(target=tarea_cajero, args=(caja,))
    hilos.append(h)
    h.start()

for h in hilos:
    h.join()

fin = time.time()
tiempo_total = fin - inicio
transacciones_por_segundo = (CAJEROS_SIMULTANEOS * VENTAS_POR_CAJERO) / tiempo_total

print("\n==================================================")
print("                RESULTADOS DEL TEST")
print("==================================================")
print(f"Tiempo Total        : {tiempo_total:.2f} segundos")
print(f"Transacciones/seg   : {transacciones_por_segundo:.2f} TPS")
print(f"Ventas Exitosas     : {exitos}")
print(f"Errores/Bloqueos    : {errores}")
print("==================================================")

if errores == 0:
    print("\n¡Excelente! MariaDB soportó el estrés perfectamente.")
    print("Ninguna base de datos SQLite por red (SMB) podría sobrevivir a esto sin arrojar 'Database is Locked'.")
else:
    print("\nHubo errores. Revisar configuración de max_connections de MariaDB.")
