import re

path = 'src/contabilidad/database.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update create tables
old_create_exp = """\
                    type TEXT DEFAULT 'variable',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'local'"""
new_create_exp = """\
                    type TEXT DEFAULT 'variable',
                    tax_amount REAL DEFAULT 0.0,
                    payment_method TEXT DEFAULT 'Efectivo Caja',
                    invoice_number TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'local'"""
content = content.replace(old_create_exp, new_create_exp)

old_create_inc = """\
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'local'"""
new_create_inc = """\
                    source TEXT,
                    tax_amount REAL DEFAULT 0.0,
                    payment_method TEXT DEFAULT 'Efectivo Caja',
                    invoice_number TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'local'"""
content = content.replace(old_create_inc, new_create_inc)


# Update add_expense
old_add_exp = """def add_expense(self, date: str, category: str, amount: float, description: str, expense_type: str = 'variable', cursor: sqlite3.Cursor = None):"""
new_add_exp = """def add_expense(self, date: str, category: str, amount: float, description: str, expense_type: str = 'variable', tax_amount: float = 0.0, payment_method: str = 'Efectivo Caja', invoice_number: str = '', cursor: sqlite3.Cursor = None):"""
content = content.replace(old_add_exp, new_add_exp)

old_ins_exp = """INSERT INTO expenses (date, category, amount, description, type) VALUES (?, ?, ?, ?, ?)"""
new_ins_exp = """INSERT INTO expenses (date, category, amount, description, type, tax_amount, payment_method, invoice_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
content = content.replace(old_ins_exp, new_ins_exp)

old_args_exp = """(date, category, amount, description, expense_type)"""
new_args_exp = """(date, category, amount, description, expense_type, tax_amount, payment_method, invoice_number)"""
content = content.replace(old_args_exp, new_args_exp)

# Update add_income
old_add_inc = """def add_income(self, date: str, amount: float, description: str, source: str, cursor: sqlite3.Cursor = None):"""
new_add_inc = """def add_income(self, date: str, amount: float, description: str, source: str, tax_amount: float = 0.0, payment_method: str = 'Efectivo Caja', invoice_number: str = '', cursor: sqlite3.Cursor = None):"""
content = content.replace(old_add_inc, new_add_inc)

old_ins_inc = """INSERT INTO income (date, amount, description, source) VALUES (?, ?, ?, ?)"""
new_ins_inc = """INSERT INTO income (date, amount, description, source, tax_amount, payment_method, invoice_number) VALUES (?, ?, ?, ?, ?, ?, ?)"""
content = content.replace(old_ins_inc, new_ins_inc)

old_args_inc = """(date, amount, description, source)"""
new_args_inc = """(date, amount, description, source, tax_amount, payment_method, invoice_number)"""
content = content.replace(old_args_inc, new_args_inc)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("database patched")
