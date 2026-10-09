import sqlite3
import datetime
import os
import calendar
import shutil
from typing import List, Dict, Any, Optional
import logging

class Database:
    """
    Clase encargada de toda la comunicación con la base de datos SQLite.
    
    NIVEL ENTERPRISE: Este es un wrapper de compatibilidad que usa internamente
    los nuevos motores enterprise (motor_asientos, motor_impuestos, etc.) pero
    mantiene la API externa para no romper el código existente.
    """
    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._enterprise_mode = False  # Se activará si se configuran los motores enterprise
        self._motor_asientos = None
        self._motor_impuestos = None
        self.init_db()
        
        # Intentar inicializar motores enterprise si están disponibles
        try:
            from src.contabilidad.motor_asientos import MotorAsientos
            from src.contabilidad.motor_impuestos import MotorImpuestos
            self._motor_asientos = MotorAsientos(db_name)
            self._motor_impuestos = MotorImpuestos(db_name)
            self._enterprise_mode = True
            logging.info("Modo Enterprise activado: usando motores contables avanzados")
        except Exception as e:
            logging.warning(f"No se pudieron inicializar motores enterprise: {e}")
            self._enterprise_mode = False

    def get_connection(self):
        """Crea una conexiÃ³n a la base de datos permitiendo buscar datos por nombre de columna."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Expenses Table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    type TEXT DEFAULT 'variable',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT \'local\'
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
                    category TEXT NOT NULL,
                    due_day INTEGER DEFAULT 1
                )
            ''')

            # Migration check for 'due_day' in fixed_costs
            cursor.execute("PRAGMA table_info(fixed_costs)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'due_day' not in columns:
                cursor.execute("ALTER TABLE fixed_costs ADD COLUMN due_day INTEGER DEFAULT 1")

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
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT \'local\'
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
            
            # Migrations for Audit fields in Contabilidad
            for table in ['expenses', 'income']:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [col[1] for col in cursor.fetchall()]
                if 'created_at' not in cols:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_at DATETIME")
                if 'created_by' not in cols:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_by TEXT DEFAULT 'local'")

            conn.commit()

    def log_audit(self, user, action, table, record_id, details):
        """Registra una acciÃ³n de auditorÃ­a avanzada."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_audit (user, action, table_affected, record_id, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user, action, table, record_id, details))
                conn.commit()
        except: pass


    def add_expense(self, date: str, category: str, amount: float, description: str, expense_type: str = 'variable', tax_amount: float = 0.0, payment_method: str = 'Efectivo Caja', invoice_number: str = '', cursor: sqlite3.Cursor = None):
        """
        Registra un nuevo gasto en la base de datos y lo anota en el historial de actividad.
        
        ENTERPRISE: Si está activado el modo enterprise, también genera un asiento contable.
        """
        if cursor:
            cursor.execute('INSERT INTO expenses (date, category, amount, description, type, tax_amount, payment_method, invoice_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                           (date, category, amount, description, expense_type, tax_amount, payment_method, invoice_number))
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO expenses (date, category, amount, description, type, tax_amount, payment_method, invoice_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                               (date, category, amount, description, expense_type, tax_amount, payment_method, invoice_number))
                cursor.execute('INSERT INTO activity_log (company, action, details) VALUES (?, ?, ?)',
                               (self.db_name.replace(".db", "").upper(), "GASTO", f"${amount:,.2f} - {category}"))
                conn.commit()
                
                # ENTERPRISE: Generar asiento contable si está activado
                if self._enterprise_mode and self._motor_asientos:
                    try:
                        from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, Moneda, EstadoAsiento
                        from datetime import datetime
                        
                        # Mapear categoría a cuenta del plan
                        cuenta_map = {
                            "Mercadería / Stock": "5.1.01.01",  # Costo de Ventas
                            "Mercadería": "5.1.01.01",
                            "Servicios": "5.1.03.02",  # Servicios
                            "Sueldos": "5.1.02.01",  # Gastos de Personal
                            "Alquiler": "5.1.03.01",  # Alquileres
                            "Mantenimiento": "5.1.03.03",  # Mantenimiento
                            "Impuestos": "5.1.06.01",  # Impuestos
                        }
                        cuenta_codigo = cuenta_map.get(category, "5.1.07.01")  # Otros Gastos por defecto
                        
                        # Determinar cuenta de activo según método de pago
                        if payment_method in ['Efectivo', 'Caja']:
                            cuenta_activo = "1.1.01.01"  # Caja
                        elif payment_method in ['Tarjeta', 'Transferencia']:
                            cuenta_activo = "1.1.01.02"  # Bancos
                        else:
                            cuenta_activo = "1.1.01.01"
                        
                        # Crear asiento de gasto
                        lineas = [
                            LineaAsiento(cuenta_codigo=cuenta_codigo, debe=amount, 
                                        descripcion=f"{category} - {description}"),
                            LineaAsiento(cuenta_codigo=cuenta_activo, haber=amount,
                                        description=f"Pago {payment_method}")
                        ]
                        
                        asiento = AsientoContable(
                            fecha=datetime.strptime(date, "%Y-%m-%d").date(),
                            tipo=TipoAsiento.MANUAL,
                            descripcion=f"Gasto: {category}",
                            lineas=lineas,
                            moneda=Moneda.ARS,
                            estado=EstadoAsiento.APROBADO,
                            referencia=f"EXP-{invoice_number}" if invoice_number else "",
                            usuario="sistema_database"
                        )
                        
                        self._motor_asientos.crear_asiento(asiento)
                    except Exception as e:
                        logging.warning(f"Error generando asiento contable para gasto: {e}")

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

    def add_income(self, date, amount, description, source, tax_amount=0.0, payment_method='Efectivo', invoice_number=''):
        """
        Registra un nuevo ingreso.
        
        ENTERPRISE: Si está activado el modo enterprise, también genera un asiento contable.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO income (date, amount, description, source, tax_amount, payment_method, invoice_number) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (date, amount, description, source, tax_amount, payment_method, invoice_number))
            cursor.execute('INSERT INTO activity_log (company, action, details) VALUES (?, ?, ?)',
                           (self.db_name.replace(".db", "").upper(), "INGRESO", f"${amount:,.2f} - {source}"))
            conn.commit()
            
            # ENTERPRISE: Generar asiento contable si está activado
            if self._enterprise_mode and self._motor_asientos:
                try:
                    from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, Moneda, EstadoAsiento
                    from datetime import datetime
                    
                    # Determinar cuenta de activo según método de pago
                    if payment_method in ['Efectivo', 'Caja']:
                        cuenta_activo = "1.1.01.01"  # Caja
                    elif payment_method in ['Tarjeta', 'Transferencia']:
                        cuenta_activo = "1.1.01.02"  # Bancos
                    else:
                        cuenta_activo = "1.1.01.01"
                    
                    # Crear asiento de ingreso
                    lineas = [
                        LineaAsiento(cuenta_codigo=cuenta_activo, debe=amount,
                                    description=f"Ingreso - {source}"),
                        LineaAsiento(cuenta_codigo="4.1.01.01", haber=amount,  # Ventas Locales
                                    description=f"{description} - {source}")
                    ]
                    
                    asiento = AsientoContable(
                        fecha=datetime.strptime(date, "%Y-%m-%d").date(),
                        tipo=TipoAsiento.MANUAL,
                        descripcion=f"Ingreso: {source}",
                        lineas=lineas,
                        moneda=Moneda.ARS,
                        estado=EstadoAsiento.APROBADO,
                        referencia=f"INC-{invoice_number}" if invoice_number else "",
                        usuario="sistema_database"
                    )
                    
                    self._motor_asientos.crear_asiento(asiento)
                except Exception as e:
                    logging.warning(f"Error generando asiento contable para ingreso: {e}")

    def get_income(self, month=None, year=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if month and year:
                month_str = f"{year}-{int(month):02d}-%"
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
                           (self.db_name.replace(".db", "").upper(), "INVERSIÃ“N", f"${amount:,.2f} - {name}"))
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

    def add_fixed_cost(self, name, amount, category, due_day=1):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO fixed_costs (name, amount, category, due_day) VALUES (?, ?, ?, ?)', (name, amount, category, due_day))
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
        """Marca una cuota de prÃ©stamo como pagada (total o parcial) y genera automÃ¡ticamente un gasto de salida."""
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
            cursor.execute("SELECT * FROM general_debts ORDER BY due_date")
            return cursor.fetchall()

    # ── MÉTODOS ENTERPRISE (Nivel Empresarial) ─────────────────────────────────────
    
    def is_enterprise_mode(self) -> bool:
        """Verifica si el modo enterprise está activado"""
        return self._enterprise_mode
    
    def get_balance_general(self, fecha: datetime.date) -> Dict:
        """
        Obtiene el balance general (estado de situación patrimonial)
        
        ENTERPRISE: Requiere modo enterprise activado
        """
        if not self._enterprise_mode or not self._motor_asientos:
            raise RuntimeError("Modo enterprise no activado. Los motores contables no están disponibles.")
        
        return self._motor_asientos.obtener_balance_general(fecha)
    
    def get_estado_resultados(self, desde: datetime.date, hasta: datetime.date) -> Dict:
        """
        Obtiene el estado de resultados (P&L)
        
        ENTERPRISE: Requiere modo enterprise activado
        """
        if not self._enterprise_mode or not self._motor_asientos:
            raise RuntimeError("Modo enterprise no activado. Los motores contables no están disponibles.")
        
        return self._motor_asientos.obtener_estado_resultados(desde, hasta)
    
    def get_mayor_general(self, cuenta_codigo: str = None, 
                           desde: datetime.date = None, 
                           hasta: datetime.date = None) -> List[Dict]:
        """
        Obtiene el mayor general
        
        ENTERPRISE: Requiere modo enterprise activado
        """
        if not self._enterprise_mode or not self._motor_asientos:
            raise RuntimeError("Modo enterprise no activado. Los motores contables no están disponibles.")
        
        return self._motor_asientos.obtener_mayor_general(cuenta_codigo, desde, hasta)
    
    def get_plan_cuentas(self, tipo: str = None) -> List[Dict]:
        """
        Obtiene el plan de cuentas
        
        ENTERPRISE: Requiere modo enterprise activado
        """
        if not self._enterprise_mode or not self._motor_asientos:
            raise RuntimeError("Modo enterprise no activado. Los motores contables no están disponibles.")
        
        from src.contabilidad.schema_fiscal import TipoCuenta
        tipo_enum = TipoCuenta(tipo) if tipo else None
        return self._motor_asientos.listar_cuentas(tipo_enum)
    
    def cargar_plan_cuentas_defecto(self):
        """
        Carga el plan de cuentas por defecto
        
        ENTERPRISE: Requiere modo enterprise activado
        """
        if not self._enterprise_mode or not self._motor_asientos:
            raise RuntimeError("Modo enterprise no activado. Los motores contables no están disponibles.")
        
        self._motor_asientos.cargar_plan_cuentas_defecto()
    
    def get_stats(self, desde: datetime.date = None, hasta: datetime.date = None) -> Dict:
        """
        Obtiene estadísticas financieras (compatibilidad con código existente)
        
        Este método mantiene la API original pero puede usar datos enterprise
        si está activado el modo.
        """
        if not self._enterprise_mode:
            # Modo legacy: usar queries directos
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total ingresos
                cursor.execute('SELECT SUM(amount) as total FROM income')
                total_income = cursor.fetchone()['total'] or 0.0
                
                # Total gastos
                cursor.execute('SELECT SUM(amount) as total FROM expenses')
                total_expenses = cursor.fetchone()['total'] or 0.0
                
                # Gastos por categoría
                cursor.execute('''
                    SELECT category, SUM(amount) as total 
                    FROM expenses 
                    GROUP BY category
                ''')
                categories = [(row['category'], row['total']) for row in cursor.fetchall()]
                
                # Gastos fijos
                cursor.execute('SELECT SUM(amount) as total FROM fixed_costs')
                fixed_expenses = cursor.fetchone()['total'] or 0.0
                
                # Inversiones
                cursor.execute('SELECT SUM(amount) as total FROM investments')
                investments_balance = cursor.fetchone()['total'] or 0.0
                
                # Balances de deudas
                balances = {}
                for table in ['loans', 'checks', 'general_debts']:
                    cursor.execute(f'SELECT SUM(amount) as total FROM {table} WHERE status IN ("pending", "partial")')
                    balances[table] = cursor.fetchone()['total'] or 0.0
                
                return {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "categories": categories,
                    "fixed_expenses": fixed_expenses,
                    "investments_balance": investments_balance,
                    "balances": balances
                }
        else:
            # Modo enterprise: usar motor de asientos
            if not desde or not hasta:
                desde = datetime.date.today().replace(day=1)
                hasta = datetime.date.today()
            
            er = self._motor_asientos.obtener_estado_resultados(desde, hasta)
            balance = self._motor_asientos.obtener_balance_general(hasta)
            
            # Convertir al formato esperado por el código existente
            categories = []
            for fila in balance['filas']:
                if fila['tipo'] == 'gasto' and fila['saldo'] > 0:
                    categories.append((fila['nombre'], fila['saldo']))
            
            return {
                "total_income": er.get('total_ingresos', 0),
                "total_expenses": er.get('total_gastos', 0),
                "categories": categories,
                "fixed_expenses": 0,  # Se calcula separadamente
                "investments_balance": 0,  # Se calcula separadamente
                "balances": {}  # Se calcula separadamente
            }
    
    def get_all_movements(self, desde: datetime.date = None, hasta: datetime.date = None) -> List:
        """
        Obtiene todos los movimientos (ingresos y gastos)
        
        Compatibilidad con código existente
        """
        movimientos = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ingresos
            cursor.execute('SELECT date, "INGRESO" as tipo, source as categoria, description, amount FROM income ORDER BY date DESC')
            for row in cursor.fetchall():
                movimientos.append((row['date'], row['tipo'], row['categoria'], row['descripcion'], row['amount']))
            
            # Gastos
            cursor.execute('SELECT date, "EGRESO" as tipo, category, description, amount FROM expenses ORDER BY date DESC')
            for row in cursor.fetchall():
                movimientos.append((row['date'], row['tipo'], row['category'], row['description'], row['amount']))
        
        # Ordenar por fecha
        movimientos.sort(key=lambda x: x[0], reverse=True)
        return movimientos
    
    def get_daily_drain(self) -> Dict:
        """
        Calcula el sangrado diario (gastos promedio por día)
        
        Compatibilidad con código existente
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Últimos 30 días
            cursor.execute('''
                SELECT AVG(amount) as avg_amount, SUM(amount) as total
                FROM expenses
                WHERE date >= date('now', '-30 days')
            ''')
            row = cursor.fetchone()
            
            return {
                "total": row['total'] or 0.0,
                "promedio": row['avg_amount'] or 0.0
            }
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
            month_str = f"{year}-{int(month):02d}-%"
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
            month_str = f"{year}-{int(month):02d}-%"
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
        """Extrae la tendencia anual para analÃ­tica visual."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            income_data = []
            expense_data = []
            for month in range(1, 13):
                period = f"{year}-{int(month):02d}-%"
                cursor.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (period,))
                income_data.append(cursor.fetchone()[0] or 0.0)
                cursor.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (period,))
                expense_data.append(cursor.fetchone()[0] or 0.0)
            return income_data, expense_data


    def get_daily_drain(self):
        import datetime
        from datetime import date
        today = date.today()
        drain = {
            'prestamos': 0.0,
            'tarjetas_prov': 0.0,
            'cheques': 0.0,
            'fijos': 0.0,
            'total': 0.0
        }

        def days_until(target_date_str):
            if not target_date_str: return 1
            try:
                t_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
                diff = (t_date - today).days
                return max(1, diff)
            except:
                return 1

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Prestamos (cuotas pendientes)
            cursor.execute("SELECT amount, due_date, paid_amount FROM installments WHERE status != 'paid'")
            for row in cursor.fetchall():
                total = row[0] or 0.0
                paid = row[2] or 0.0
                rem = total - paid
                if rem > 0:
                    d = days_until(row[1])
                    drain['prestamos'] += (rem / d)

            # 2. General Debts
            cursor.execute("SELECT amount, due_date, paid_amount FROM general_debts WHERE status != 'paid'")
            for row in cursor.fetchall():
                total = row[0] or 0.0
                paid = row[2] or 0.0
                rem = total - paid
                if rem > 0:
                    d = days_until(row[1])
                    drain['tarjetas_prov'] += (rem / d)

            # 3. Checks
            cursor.execute("SELECT amount, due_date, paid_amount FROM checks WHERE status != 'paid'")
            for row in cursor.fetchall():
                total = row[0] or 0.0
                paid = row[2] or 0.0
                rem = total - paid
                if rem > 0:
                    d = days_until(row[1])
                    drain['cheques'] += (rem / d)

            # 4. Fixed Costs
            cursor.execute("SELECT amount, due_day FROM fixed_costs")
            for row in cursor.fetchall():
                amount = row[0] or 0.0
                due_day = row[1] or 1
                try:
                    due_day = int(due_day)
                except:
                    due_day = 1

                if due_day < today.day:
                    if today.month == 12:
                        y = today.year + 1
                        m = 1
                    else:
                        y = today.year
                        m = today.month + 1
                else:
                    y = today.year
                    m = today.month

                try:
                    target = datetime.date(y, m, due_day)
                except ValueError:
                    if m == 12:
                        target = datetime.date(y+1, 1, 1)
                    else:
                        target = datetime.date(y, m+1, 1)

                diff = (target - today).days
                d = max(1, diff)
                drain['fijos'] += (amount / d)

        drain['total'] = drain['prestamos'] + drain['tarjetas_prov'] + drain['cheques'] + drain['fijos']
        return drain

    def get_stats(self, desde=None, hasta=None, month=None, year=None):
        """Calcula los totales de ingresos, egresos y saldos pendientes para los cuadros del Dashboard."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if desde is None and hasta is None:
                if not month or not year:
                    today = datetime.date.today()
                    month, year = today.month, today.year
                period_str = f"{year}-{int(month):02d}-%"
                desde = f"{year}-{int(month):02d}-01 00:00:00"
                hasta = f"{year}-{int(month):02d}-31 23:59:59"
                date_filter = "date LIKE ?"
                params_filter = (period_str,)
            else:
                date_filter = "date BETWEEN ? AND ?"
                params_filter = (desde, hasta)

            # Expenses for the period (excluding debt payments to keep P&L accurate)
            cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {date_filter} AND type != 'tesoreria'", params_filter)
            total_expenses = cursor.fetchone()[0] or 0.0

            cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {date_filter} AND type = 'fijo'", params_filter)
            fixed_expenses = cursor.fetchone()[0] or 0.0

            cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {date_filter} AND type = 'variable'", params_filter)
            variable_expenses = cursor.fetchone()[0] or 0.0

            cursor.execute(f"SELECT SUM(amount) FROM expenses WHERE {date_filter} AND type = 'tesoreria'", params_filter)
            financial_expenses = cursor.fetchone()[0] or 0.0

            # Income for the period
            cursor.execute(f"SELECT SUM(amount) FROM income WHERE {date_filter}", params_filter)
            total_income = cursor.fetchone()[0] or 0.0

            # Category Breakdown (OPEX only)
            cursor.execute(f'''
                SELECT category, SUM(amount) FROM expenses
                WHERE {date_filter} AND type != 'tesoreria'
                GROUP BY category
                ORDER BY SUM(amount) DESC
            ''', params_filter)
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

            cursor.execute("SELECT SUM(amount) FROM investments")
            inv_balance = cursor.fetchone()[0] or 0.0

            return {
                "total_expenses": total_expenses,
                "fixed_expenses": fixed_expenses,
                "variable_expenses": variable_expenses,
                "financial_expenses": financial_expenses,
                "total_income": total_income,
                "categories": categories,
                "balances": {
                    "PrÃ©stamos": loan_balance,
                    "Cheques": check_balance,
                    "Tarjetas": card_balance,
                    "Proveedores": prov_balance
                },
                "investments_balance": inv_balance
            }

    def get_pure_accounting_stats(self, date_obj=None):
        """Obtiene mÃ©tricas de contabilidad pura: Total del dÃ­a, mes y aÃ±o acumulado."""
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

    def get_all_movements(self, desde=None, hasta=None, month=None, year=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if desde is None and hasta is None:
                period_str = f"{year}-{int(month):02d}-%" if month and year else "%"
                date_filter = "date LIKE ?"
                date_filter_due = "due_date LIKE ?"
                params_filter = (period_str, period_str, period_str, period_str, period_str)
            else:
                date_filter = "date BETWEEN ? AND ?"
                date_filter_due = "due_date BETWEEN ? AND ?"
                params_filter = (desde, hasta, desde, hasta, desde, hasta, desde, hasta, desde, hasta)

            cursor.execute(f'''
                SELECT date, 'INGRESO' as type, source as cat, description, amount, id, 'Pagado' as status FROM income
                WHERE {date_filter}
                UNION ALL
                SELECT date, 'EGRESO' as type, category as cat, description, -amount as amount, id, 'Pagado' as status FROM expenses
                WHERE {date_filter}
                UNION ALL
                SELECT due_date as date, 'DEUDA' as type, category as cat, name as description, -amount as amount, id,
                       CASE WHEN status = 'pending' THEN 'Pendiente'
                            WHEN status = 'partial' THEN 'Parcial'
                            ELSE 'Pagado' END as status
                FROM general_debts
                WHERE {date_filter_due} AND status != 'paid'
                UNION ALL
                SELECT due_date as date, 'CHEQUE' as type, 'Cheque' as cat, bank || ' - ' || recipient as description, -amount as amount, id,
                       CASE WHEN status = 'pending' THEN 'Pendiente'
                            ELSE 'Pagado' END as status
                FROM checks
                WHERE {date_filter_due} AND status != 'paid'
                UNION ALL
                SELECT i.due_date as date, 'PRÃ‰STAMO' as type, l.category as cat, 'Cuota ' || i.number || ' - ' || l.name as description, -i.amount as amount, i.id,
                       CASE WHEN i.status = 'pending' THEN 'Pendiente'
                            WHEN i.status = 'partial' THEN 'Parcial'
                            ELSE 'Pagado' END as status
                FROM installments i
                JOIN loans l ON i.loan_id = l.id
                WHERE i.{date_filter_due} AND i.status != 'paid'
                ORDER BY date DESC
            ''', params_filter)
            return cursor.fetchall()


