# -*- coding: utf-8 -*-
import os

with open('src/jefe/promedios/motor_global_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix exportar_a_inventario indices just in case it didn't catch it
content = content.replace('precio_base_str = str(row_data[4])', 'precio_base_str = str(row_data[3])')

# Fix sincronizar_inventario completely
old_sync_block = '''            if cfg.get("precio", 0) > 0:
                filas[r_idx][4] = f"{cfg['precio']:,.2f}"
                actualizados += 1
            if cfg.get("precio_mayoreo", 0) > 0:
                filas[r_idx][5] = f"{cfg['precio_mayoreo']:,.2f}"
            if cfg.get("cant_mayoreo", 0) > 0:
                filas[r_idx][6] = f"{cfg['cant_mayoreo']:,.2f}"'''
new_sync_block = '''            if cfg.get("precio", 0) > 0:
                filas[r_idx][3] = f"{cfg['precio']:,.2f}"
                actualizados += 1
            if cfg.get("precio_mayoreo", 0) > 0:
                filas[r_idx][5] = f"{cfg['precio_mayoreo']:,.2f}"
            if cfg.get("cant_mayoreo", 0) > 0:
                filas[r_idx][6] = f"{cfg['cant_mayoreo']:,.2f}"'''
content = content.replace(old_sync_block, new_sync_block)

# If it had [3] but missed the others? Just to be safe, I'll regex it or use a solid replace.
with open('src/jefe/promedios/motor_global_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('src/motor_descuentos/mayoreo/motor.py', 'r', encoding='utf-8') as f:
    m_content = f.read()

# Make obtener_por_nombre case insensitive
m_content = m_content.replace('WHERE nombre=?', 'WHERE LOWER(nombre)=LOWER(?)')

# Make aplicar_desde_promedios case insensitive and fix new product logic
old_aplicar = '''        try:
            res = self.db.execute_query("SELECT id FROM productos WHERE nombre=?", (nombre,))
            if res:
                return bool(self.db.execute_non_query(
                    "UPDATE productos SET precio=?, costo=?, cant_mayoreo=?, precio_mayoreo=? WHERE nombre=?",
                    (precio, costo, cant_mayoreo, precio_mayoreo, nombre),
                ))
            import random
            cod = f"PROM-{random.randint(1000, 9999)}"
            return bool(self.db.execute_non_query(
                "INSERT INTO productos (nombre, precio, cant_mayoreo, precio_mayoreo, "
                "categoria, unidad, codigo, es_pesable, costo) "
                "VALUES (?, ?, ?, ?, ?, 'KG', ?, 1, ?)",
                (nombre, precio, cant_mayoreo, precio_mayoreo, (categoria or "").upper(), cod, costo),
            ))'''

new_aplicar = '''        try:
            res = self.db.execute_query("SELECT id FROM productos WHERE LOWER(nombre)=LOWER(?)", (nombre,))
            if res:
                return bool(self.db.execute_non_query(
                    "UPDATE productos SET precio=?, costo=?, cant_mayoreo=?, precio_mayoreo=? WHERE LOWER(nombre)=LOWER(?)",
                    (precio, costo, cant_mayoreo, precio_mayoreo, nombre),
                ))
            import random
            cod = f"PROM-{random.randint(10000, 99999)}"
            return bool(self.db.execute_non_query(
                "INSERT INTO productos (nombre, precio, cant_mayoreo, precio_mayoreo, "
                "categoria, unidad, codigo, es_pesable, costo) "
                "VALUES (?, ?, ?, ?, ?, 'KG', ?, 1, ?)",
                (nombre, precio, cant_mayoreo, precio_mayoreo, (categoria or "").upper(), cod, costo),
            ))'''

m_content = m_content.replace(old_aplicar, new_aplicar)

with open('src/motor_descuentos/mayoreo/motor.py', 'w', encoding='utf-8') as f:
    f.write(m_content)

print('Updated motor and promedios indices')
