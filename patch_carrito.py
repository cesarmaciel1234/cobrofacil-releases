import re

with open('src/cajero/paso5_terminal/logica/carrito_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace buscar_productos
new_buscar_productos = '''    def buscar_productos(self, txt):
        """Busca productos por ID o aproximacion de nombre. Retorna lista de diccionarios."""
        if txt.isdigit():
            res = db_manager.execute_query(
                "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
                "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
                "es_pesable, unidad, departamento FROM productos WHERE id = ? OR COALESCE(codigo,'') LIKE ? OR nombre LIKE ? LIMIT 5",
                (int(txt), f"%{txt}%", f"%{txt}%"),
            )
        else:
            res = db_manager.execute_query(
                "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
                "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
                "es_pesable, unidad, departamento FROM productos WHERE nombre LIKE ? OR COALESCE(codigo,'') LIKE ? LIMIT 5",
                (f"%{txt}%", f"%{txt}%"),
            )
        return res or []'''

text = re.sub(
    r'    def buscar_productos\(self, txt\):[\s\S]*?\(txt, f"%\{txt\}%"\),\s*\)\s*or\s*\[\]',
    new_buscar_productos,
    text
)

# Replace buscar_producto_exacto
new_buscar_exacto = '''    def buscar_producto_exacto(self, txt):
        """Busca un producto exactamente por su ID o codigo de barras."""
        if txt.isdigit():
            res = db_manager.execute_query(
                "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
                "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
                "es_pesable, unidad, departamento FROM productos WHERE id = ? OR codigo = ?",
                (int(txt), txt),
            )
        else:
            res = db_manager.execute_query(
                "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
                "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
                "es_pesable, unidad, departamento FROM productos WHERE codigo = ?",
                (txt,),
            )
        return res[0] if res else None'''

text = re.sub(
    r'    def buscar_producto_exacto\(self, txt\):[\s\S]*?return res\[0\] if res else None',
    new_buscar_exacto,
    text
)

with open('src/cajero/paso5_terminal/logica/carrito_service.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Optimized carrito_service.py')
