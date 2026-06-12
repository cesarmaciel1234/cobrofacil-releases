import sys
import random
from datetime import datetime, timedelta

sys.path.append('src')
from utils.db import db_manager

def generar_datos_prueba():
    print("Iniciando generación de datos de prueba...")
    db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 0;")
    
    # 1. Crear departamentos
    deptos = ['ALMACEN', 'BEBIDAS', 'LACTEOS', 'CARNES', 'LIMPIEZA']
    for d in deptos:
        db_manager.execute_non_query("INSERT IGNORE INTO departamentos (nombre) VALUES (?)", (d,))
        
    print("Departamentos creados.")
    
    # 2. Crear productos
    productos = []
    for d in deptos:
        for i in range(1, 21):
            cod = f"{d[:3]}-{i:03d}"
            nom = f"Producto {i} de {d}"
            costo = round(random.uniform(50, 500), 2)
            precio = round(costo * 1.3, 2)
            stock = random.randint(10, 1000)
            
            db_manager.execute_non_query(
                "INSERT INTO productos (codigo, nombre, precio, costo, stock, departamento) VALUES (?, ?, ?, ?, ?, ?)",
                (cod, nom, precio, costo, stock, d)
            )
    
    # Recuperar IDs de productos creados
    prods_db = db_manager.execute_query("SELECT id, nombre, precio, costo FROM productos")
    print(f"{len(prods_db)} productos creados.")

    # 3. Crear 50,000 Ventas
    # Use bulk insert for speed
    ventas_data = []
    detalles_data = []
    
    start_date = datetime.now() - timedelta(days=365)
    
    print("Generando 50,000 ventas...")
    
    for v_id in range(1, 50001):
        # Random date in the last year
        delta_days = random.randint(0, 365)
        delta_seconds = random.randint(0, 86400)
        v_date = start_date + timedelta(days=delta_days, seconds=delta_seconds)
        v_date_str = v_date.strftime('%Y-%m-%d %H:%M:%S')
        
        estado = random.choice(['COMPLETADA', 'COMPLETADA', 'COMPLETADA', 'COMPLETADA', 'CANCELADA'])
        metodo = random.choice(['Efectivo', 'Tarjeta', 'MercadoPago', 'Transferencia'])
        cajero = random.choice(['admin', 'cajero1', 'cajero2'])
        
        num_items = random.randint(1, 5)
        total_venta = 0
        costo_venta = 0
        
        v_detalles = []
        for _ in range(num_items):
            p = random.choice(prods_db)
            cant = random.randint(1, 5)
            subtotal = round(cant * p['precio'], 2)
            
            total_venta += subtotal
            costo_venta += (cant * p['costo'])
            
            v_detalles.append((v_id, p['id'], p['nombre'], cant, p['precio'], subtotal))
            
        ventas_data.append((v_id, v_date_str, total_venta, 0, 0, metodo, cajero, estado))
        detalles_data.extend(v_detalles)

        if v_id % 5000 == 0:
            print(f"Generadas {v_id} ventas en memoria...")

    print("Insertando ventas en la base de datos (Bulk)...")
    db_manager.execute_many(
        "INSERT INTO ventas (id, fecha, total, descuento, recargo, metodo_pago, usuario, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ventas_data
    )
    
    print("Insertando detalles de ventas en la base de datos (Bulk)...")
    db_manager.execute_many(
        "INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
        detalles_data
    )
    
    db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 1;")
    print("¡1 millón simulado! (50,000 tickets creados exitosamente para stress test)")

if __name__ == "__main__":
    generar_datos_prueba()
