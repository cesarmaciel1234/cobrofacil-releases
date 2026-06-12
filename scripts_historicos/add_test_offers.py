import sys
import os

# Append project root to path so imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.base_de_datos.database import DatabaseManager

db = DatabaseManager()

# Ensure products exist and set offers
test_products = [
    ("Asado", 6500.00, 5000.00),     # Precio Base 6500, Oferta 5000
    ("Vacío", 7200.00, 6800.00),     # Precio Base 7200, Oferta 6800
    ("Matambre", 6000.00, 0.00),     # Precio Base 6000, Sin Oferta
    ("Pechito", 4500.00, 3999.00),   # Precio Base 4500, Oferta 3999 (Cerdo)
    ("Suprema", 3500.00, 2999.00)    # Precio Base 3500, Oferta 2999 (Pollo)
]

for nombre, precio, precio_oferta in test_products:
    # Check if exists
    res = db.execute_query("SELECT id FROM productos WHERE nombre = ?", (nombre,))
    if res and len(res) > 0:
        db.execute_non_query("UPDATE productos SET precio = ?, precio_oferta = ? WHERE nombre = ?", (precio, precio_oferta, nombre))
    else:
        db.execute_non_query("INSERT INTO productos (nombre, precio, precio_oferta, categoria) VALUES (?, ?, ?, ?)", (nombre, precio, precio_oferta, "CARNES"))

print("Test offers inserted successfully.")
