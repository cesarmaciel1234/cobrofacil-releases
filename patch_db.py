import sqlite3

def add_columns_to_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Gastos (expenses)
    cursor.execute("PRAGMA table_info(expenses)")
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'tax_amount' not in cols:
        cursor.execute("ALTER TABLE expenses ADD COLUMN tax_amount REAL DEFAULT 0.0")
    if 'payment_method' not in cols:
        cursor.execute("ALTER TABLE expenses ADD COLUMN payment_method TEXT DEFAULT 'Efectivo Caja'")
    if 'invoice_number' not in cols:
        cursor.execute("ALTER TABLE expenses ADD COLUMN invoice_number TEXT DEFAULT ''")
        
    # 2. Ingresos (income)
    cursor.execute("PRAGMA table_info(income)")
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'tax_amount' not in cols:
        cursor.execute("ALTER TABLE income ADD COLUMN tax_amount REAL DEFAULT 0.0")
    if 'payment_method' not in cols:
        cursor.execute("ALTER TABLE income ADD COLUMN payment_method TEXT DEFAULT 'Efectivo Caja'")
    if 'invoice_number' not in cols:
        cursor.execute("ALTER TABLE income ADD COLUMN invoice_number TEXT DEFAULT ''")
        
    conn.commit()
    conn.close()

add_columns_to_db('src/contabilidad/database.db')
print("Columns added to database.")
