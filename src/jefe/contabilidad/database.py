import sqlite3
import datetime
import os
import calendar
import shutil
from typing import List, Dict, Any, Optional
import logging

class Database:
    """Clase encargada de toda la comunicación con la base de datos SQLite."""
    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Crea una conexión a la base de datos permitiendo buscar datos por nombre de columna."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Expenses Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    type TEXT DEFAULT 'variable'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    company TEXT,
                    action TEXT,
                    details TEXT
                )
            ''')
            
            # Migration check for 'type'
            cursor.execute("PRAGMA table_info(expenses)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'type' not in columns:
                cursor.execute("ALTER TABLE expenses ADD COLUMN type TEXT DEFAULT 'variable'")

            # 2. Fixed Costs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fixed_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL
                )
            ''')

            # 3. Loans
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    capital REAL DEFAULT 0.0,
                    interest REAL DEFAULT 0.0,
                    category TEXT NOT NULL,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Migration check for 'capital' and 'interest'
            cursor.execute("PRAGMA table_info(loans)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'capital' not in columns:
                cursor.execute("ALTER TABLE loans ADD COLUMN capital REAL DEFAULT 0.0")
            if 'interest' not in columns:
                cursor.execute("ALTER TABLE loans ADD COLUMN interest REAL DEFAULT 0.0")

            # 4. Installments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS installments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER,
                    number INTEGER,
                    amount REAL,
                    due_date TEXT,
                    status TEXT DEFAULT 'pending',
                    paid_date TEXT,
                    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
                )
            ''')

            # 5. Checks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank TEXT,
                    number TEXT,
                    amount REAL,
                    due_date TEXT,
                    recipient TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')

            # 6. General Debts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS general_debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    due_date TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')

            # Migrations for partial payments (paid_amount)
            for table in ['installments', 'checks', 'general_debts']:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [col[1] for col in cursor.fetchall()]
                if 'paid_amount' not in cols:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN paid_amount REAL DEFAULT 0.0")

            # 7. Income Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    source TEXT
                )
            ''')

            # 8. Investments Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT
                )
            ''')


            # 11. Audit Logs Pro (Nivel 4)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user TEXT,
                    action TEXT,
                    table_affected TEXT,
                    record_id INTEGER,
                    details TEXT
                )
            ''')
            conn.commit()

    def log_audit(self, user, action, table, record_id, details):
        """Registra una acción de auditoría avanzada."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_audit (user, action, table_affected, record_id, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user, action, table, record_id, details))
                conn.commit()
        except: pass


    def add_expense(self, date: str, category: str, amount: float, description: str, expense_type: str = 'variable', cursor: sqlite3.Cursor = None):
        """Registra un nuevo gasto en la base de datos y lo anota en el historial de actividad."""
        if cursor:
            cursor.execute('INSERT INTO expenses (date, category, amount, description, type) VALUES (?, ?, ?, ?, ?)', 
                           (date, category, amount, description, expense_type))
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO expenses (date, category, amount, description, type) VALUES (?, ?, ?, ?, ?)', 
                               (date, category, amount, description, expense_type))
                cursor.execute('INSERT INTO activity_log (company, action, details) VALUES (?, ?, ?)',
                               (self.db_name.replace(".db", "").upper(), "GASTO", f"${amount:,.2f} - {category}"))
                conn.commit()

    def get_expenses(self, expense_type: Optional[str] = None) -> List[sqlite3.Row]:
        """Recupera la lista de gastos, pudiendo filtrar por fijos o variables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if expense_type:
                cursor.execute('SELECT * FROM expenses WHERE type = ? ORDER BY date DESC', (expense_type,))
            else:
                cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
            return cursor.fetchall()

    def delete_expense(self, expense_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()

    def update_expense(self, id, amount, description, category):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE expenses SET amount = ?, description = ?, category = ? WHERE id = ?', 
                           (amount, description, category, id))
            conn.commit()

    def add_income(self, date, amount, description, source):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO income (date, amount, description, source) VALUES (?, ?, ?, ?)', 
                           (date, amount, description, source))
            cursor.execute('INSERT INTO activity_log (company, action, details) VALUES (?, ?, ?)',
                           (self.db_name.replace(".db", "").upper(), "INGRESO", f"${amount:,.2f} - {source}"))
            conn.commit()

    def get_income(self, month=None, year=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if month and year:
                month_str = f"{year}-{month:02d}-%"
                cursor.execute('SELECT * FROM income WHERE date LIKE ? ORDER BY date DESC', (month_str,))
            else:
                cursor.execute('SELECT * FROM income ORDER BY date DESC')
            return cursor.fetchall()

    def delete_income(self, income_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM income WHERE id = ?', (income_id,))
            conn.commit()

    def update_income(self, id, amount, description, source):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE income SET amount = ?, description = ?, source = ? WHERE id = ?', 
                           (amount, description, source, id))
            conn.commit()

    def add_investment(self, date, name, amount, category):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO investments (date, name, amount, category) VALUES (?, ?, ?, ?)', 
                           (date, name, amount, category))
            cursor.execute('INSERT INTO activity_log (company, action, details) VALUES (?, ?, ?)',
                           (self.db_name.replace(".db", "").upper(), "INVERSIÓN", f"${amount:,.2f} - {name}"))
            conn.commit()

    def get_investments(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM investments ORDER BY date DESC')
            return cursor.fetchall()

    def delete_investment(self, inv_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM investments WHERE id = ?', (inv_id,))
            conn.commit()

    def add_fixed_cost(self, name, amount, category):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO fixed_costs (name, amount, category) VALUES (?, ?, ?)', (name, amount, category))
            conn.commit()

    def get_fixed_costs(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM fixed_costs')
            return cursor.fetchall()

    def delete_fixed_cost(self, cost_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM fixed_costs WHERE id = ?', (cost_id,))
            conn.commit()

    def add_loan(self, name, total_amount, capital, interest, category, installments_count, first_due_date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO loans (name, total_amount, capital, interest, category) 
                VALUES (?, ?, ?, ?, ?)
            ''', (name, total_amount, capital, interest, category))
            loan_id = cursor.lastrowid
            inst_amount = total_amount / installments_count
            
            if first_due_date:
                start_date = datetime.datetime.strptime(first_due_date, "%Y-%m-%d").date()
            else:
                start_date = datetime.date.today()

            for i in range(1, installments_count + 1):
                # Increment month from start_date
                month = start_date.month - 1 + (i - 1)
                year = start_date.year + month // 12
                month = month % 12 + 1
                day = min(start_date.day, calendar.monthrange(year, month)[1])
                due_date = datetime.date(year, month, day).strftime("%Y-%m-%d")
                
                cursor.execute('INSERT INTO installments (loan_id, number, amount, due_date) VALUES (?, ?, ?, ?)', 
                               (loan_id, i, inst_amount, due_date))
            conn.commit()

    def get_loans(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM loans')
            return cursor.fetchall()

    def delete_loan(self, loan_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Installments will be deleted automatically due to ON DELETE CASCADE
            cursor.execute('DELETE FROM loans WHERE id = ?', (loan_id,))
            conn.commit()

    def get_installments(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, l.name, l.capital, l.interest, l.total_amount, 
                       (SELECT COUNT(*) FROM installments WHERE loan_id = l.id) as total_inst
                FROM installments i 
                JOIN loans l ON i.loan_id = l.id 
                WHERE i.status IN ('pending', 'partial') ORDER BY i.due_date
            ''')
            return cursor.fetchall()

    def update_installment_date(self, inst_id, new_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE installments SET due_date = ? WHERE id = ?', (new_date, inst_id))
            conn.commit()

    def pay_installment(self, inst_id, payment_amount=None):
        """Marca una cuota de préstamo como pagada (total o parcial) y genera automáticamente un gasto de salida."""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM installments WHERE id = ?', (inst_id,))
                inst = cursor.fetchone()
                if inst:
                    loan_id = inst['loan_id']
                    cursor.execute('SELECT name, category FROM loans WHERE id = ?', (loan_id,))
                    loan = cursor.fetchone()
                    today = datetime.date.today().strftime("%Y-%m-%d")
                    
                    total = inst['amount']
                    already_paid = inst['paid_amount'] if 'paid_amount' in inst.keys() else 0.0
                    remaining = total - already_paid
                    
                    amount = float(payment_amount) if payment_amount is not None else remaining
                    if amount <= 0: return
                    
                    new_paid = already_paid + amount
                    status = 'paid' if new_paid >= total else 'partial'
                    
                    cursor.execute("UPDATE installments SET status = ?, paid_amount = ?, paid_date = ? WHERE id = ?", 
                                   (status, new_paid, today, inst_id))
                    
                    desc = f"Pago {'Parcial ' if status == 'partial' else ''}Cuota {inst['number']} - {loan['name']}"
                    self.add_expense(today, loan['category'], amount, desc, 'tesoreria', cursor=cursor)
                    conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                logging.error(f"Error al pagar cuota {inst_id}: {e}")
                raise

    def add_check(self, bank, number, amount, due_date, recipient):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO checks (bank, number, amount, due_date, recipient) VALUES (?, ?, ?, ?, ?)', 
                           (bank, number, amount, due_date, recipient))
            conn.commit()

    def get_checks(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM checks WHERE status IN ('pending', 'partial') ORDER BY due_date")
            return cursor.fetchall()

    def pay_check(self, check_id, payment_amount=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM checks WHERE id = ?', (check_id,))
            check = cursor.fetchone()
            if check:
                today = datetime.date.today().strftime("%Y-%m-%d")
                total = check['amount']
                already_paid = check['paid_amount'] if 'paid_amount' in check.keys() else 0.0
                remaining = total - already_paid
                
                amount = float(payment_amount) if payment_amount is not None else remaining
                if amount <= 0: return
                
                new_paid = already_paid + amount
                status = 'paid' if new_paid >= total else 'partial'
                
                cursor.execute("UPDATE checks SET status = ?, paid_amount = ? WHERE id = ?", (status, new_paid, check_id))
                desc = f"Cobro {'Parcial ' if status == 'partial' else ''}Cheque {check['number']} - {check['bank']}"
                self.add_expense(today, "Cheques", amount, desc, 'tesoreria', cursor=cursor)
                conn.commit()

    def add_general_debt(self, name, category, amount, due_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO general_debts (name, category, amount, due_date) VALUES (?, ?, ?, ?)', 
                           (name, category, amount, due_date))
            conn.commit()

    def get_general_debts(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM general_debts WHERE status IN ("pending", "partial")')
            return cursor.fetchall()

    def pay_general_debt(self, debt_id, payment_amount=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM general_debts WHERE id = ?', (debt_id,))
            debt = cursor.fetchone()
            if debt:
                today = datetime.date.today().strftime("%Y-%m-%d")
                total = debt['amount']
                already_paid = debt['paid_amount'] if 'paid_amount' in debt.keys() else 0.0
                remaining = total - already_paid
                
                amount = float(payment_amount) if payment_amount is not None else remaining
                if amount <= 0: return
                
                new_paid = already_paid + amount
                status = 'paid' if new_paid >= total else 'partial'
                
                cursor.execute("UPDATE general_debts SET status = ?, paid_amount = ? WHERE id = ?", (status, new_paid, debt_id))
                desc = f"Pago {'Parcial ' if status == 'partial' else ''}{debt['category']} - {debt['name']}"
                self.add_expense(today, debt['category'], amount, desc, 'tesoreria', cursor=cursor)
                conn.commit()

    def delete_general_debt(self, debt_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM general_debts WHERE id = ?', (debt_id,))
            conn.commit()

    def backup_database(self, destination):
        try:
            shutil.copy2(self.db_name, destination)
            return True
        except:
            return False

    def check_if_fixed_costs_applied(self, month, year):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if any expense of type 'fijo' exists for this month/year
            month_str = f"{year}-{month:02d}-%"
            cursor.execute("SELECT id FROM expenses WHERE type = 'fijo' AND date LIKE ?", (month_str,))
            return cursor.fetchone() is not None

    def get_latest_activity(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT timestamp, action, details, company FROM activity_log ORDER BY timestamp DESC LIMIT 10')
                return cursor.fetchall()
        except: return []

    def delete_fixed_costs_for_period(self, month, year):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            month_str = f"{year}-{month:02d}-%"
            cursor.execute("DELETE FROM expenses WHERE type = 'fijo' AND date LIKE ?", (month_str,))
            conn.commit()

    def search_expenses(self, query):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search = f"%{query}%"
            cursor.execute('''
                SELECT * FROM expenses 
                WHERE category LIKE ? OR description LIKE ? 
                ORDER BY date DESC
            ''', (search, search))
            return cursor.fetchall()

    def get_trend_data(self, year: int):
        """Extrae la tendencia anual para analítica visual."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            income_data = []
            expense_data = []
            for month in range(1, 13):
                period = f"{year}-{month:02d}-%"
                cursor.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (period,))
                income_data.append(cursor.fetchone()[0] or 0.0)
                cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (period,))
                expense_data.append(cursor.fetchone()[0] or 0.0)
            return income_data, expense_data

    def get_stats(self, month=None, year=None):
        """Calcula los totales de ingresos, egresos y saldos pendientes para los cuadros del Dashboard."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if not month or not year:
                today = datetime.date.today()
                month, year = today.month, today.year
            
            period_str = f"{year}-{month:02d}"
            
            # Expenses for the period
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{period_str}-%",))
            total_expenses = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ? AND type = 'fijo'", (f"{period_str}-%",))
            fixed_expenses = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ? AND type = 'variable'", (f"{period_str}-%",))
            variable_expenses = cursor.fetchone()[0] or 0.0
            
            # Income for the period
            cursor.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (f"{period_str}-%",))
            total_income = cursor.fetchone()[0] or 0.0
            
            # Category Breakdown
            cursor.execute('''
                SELECT category, SUM(amount) FROM expenses 
                WHERE date LIKE ? 
                GROUP BY category 
                ORDER BY SUM(amount) DESC
            ''', (f"{period_str}-%",))
            categories = cursor.fetchall()

            # Global Balances (not tied to period)
            cursor.execute("SELECT SUM(amount) FROM installments WHERE status = 'pending'")
            loan_balance = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(amount) FROM checks WHERE status = 'pending'")
            check_balance = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(amount) FROM general_debts WHERE category = 'Tarjeta' AND status = 'pending'")
            card_balance = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(amount) FROM general_debts WHERE category = 'Proveedor' AND status = 'pending'")
            prov_balance = cursor.fetchone()[0] or 0.0
            
            return {
                "total_expenses": total_expenses,
                "fixed_expenses": fixed_expenses,
                "variable_expenses": variable_expenses,
                "total_income": total_income,
                "balance": total_income - total_expenses,
                "categories": categories,
                "balances": {
                    "Préstamos": loan_balance,
                    "Cheques": check_balance,
                    "Tarjetas": card_balance,
                    "Proveedores": prov_balance
                }
            }

    def get_pure_accounting_stats(self, date_obj=None):
        """Obtiene métricas de contabilidad pura: Total del día, mes y año acumulado."""
        if not date_obj:
            date_obj = datetime.date.today()
        
        day_str = date_obj.strftime("%Y-%m-%d")
        month_str = date_obj.strftime("%Y-%m")
        year_str = date_obj.strftime("%Y")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # --- DAILY ---
            cursor.execute("SELECT SUM(amount) FROM income WHERE date = ?", (day_str,))
            daily_inc = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE date = ?", (day_str,))
            daily_exp = cursor.fetchone()[0] or 0.0
            
            # --- MONTHLY ---
            cursor.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (f"{month_str}-%",))
            monthly_inc = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{month_str}-%",))
            monthly_exp = cursor.fetchone()[0] or 0.0
            
            # --- ANNUAL ---
            cursor.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (f"{year_str}-%",))
            annual_inc = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{year_str}-%",))
            annual_exp = cursor.fetchone()[0] or 0.0
            
            return {
                "day": {"inc": daily_inc, "exp": daily_exp, "net": daily_inc - daily_exp},
                "month": {"inc": monthly_inc, "exp": monthly_exp, "net": monthly_inc - monthly_exp},
                "year": {"inc": annual_inc, "exp": annual_exp, "net": annual_inc - annual_exp}
            }

    def get_all_movements(self, month=None, year=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            period_str = f"{year}-{month:02d}-%" if month and year else "%"
            
            cursor.execute('''
                SELECT date, 'INGRESO' as type, source as cat, description, amount, id, 'Pagado' as status FROM income 
                WHERE date LIKE ?
                UNION ALL
                SELECT date, 'EGRESO' as type, category as cat, description, -amount as amount, id, 'Pagado' as status FROM expenses
                WHERE date LIKE ?
                UNION ALL
                SELECT due_date as date, 'DEUDA' as type, category as cat, name as description, -amount as amount, id, 
                       CASE WHEN status = 'pending' THEN 'Pendiente' 
                            WHEN status = 'partial' THEN 'Parcial'
                            ELSE 'Pagado' END as status
                FROM general_debts
                WHERE due_date LIKE ? AND status != 'paid'
                ORDER BY date DESC
            ''', (period_str, period_str, period_str))
            return cursor.fetchall()
