with open('src/jefe/promedios/motor_global_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix exportar_a_inventario indices
content = content.replace('precio_base_str = str(row_data[4])', 'precio_base_str = str(row_data[3])')

# Fix sincronizar_inventario indices
old_sync = '''            if cfg.get("precio", 0) > 0:
                filas[r_idx][4] = f"{cfg['precio']:,.2f}"
                actualizados += 1
            if cfg.get("precio_mayoreo", 0) > 0:
                filas[r_idx][5] = f"{cfg['precio_mayoreo']:,.2f}"
            if cfg.get("cant_mayoreo", 0) > 0:
                filas[r_idx][6] = f"{cfg['cant_mayoreo']:,.2f}"'''
new_sync = '''            if cfg.get("precio", 0) > 0:
                filas[r_idx][3] = f"{cfg['precio']:,.2f}"
                actualizados += 1
            if cfg.get("precio_mayoreo", 0) > 0:
                filas[r_idx][5] = f"{cfg['precio_mayoreo']:,.2f}"
            if cfg.get("cant_mayoreo", 0) > 0:
                filas[r_idx][6] = f"{cfg['cant_mayoreo']:,.2f}"'''
content = content.replace(old_sync, new_sync)

with open('src/jefe/promedios/motor_global_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Indices fixed')
