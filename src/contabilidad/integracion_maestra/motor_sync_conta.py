import sqlite3
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from src.base_de_datos.database import db_manager
import time
import uuid

class MotorSyncConta(QThread):
    sync_finished = pyqtSignal(int, int) # (pushed_count, pulled_count)
    sync_error = pyqtSignal(str)

    def __init__(self, db_conta, parent=None):
        super().__init__(parent)
        self.db_conta = db_conta
        self.running = True

    def _asegurar_esquemas(self):
        # 1. Esquema en MariaDB (Maestra)
        try:
            db_manager.execute_non_query("""
                CREATE TABLE IF NOT EXISTS conta_expenses (
                    sync_id VARCHAR(50) PRIMARY KEY,
                    date VARCHAR(20),
                    category VARCHAR(100),
                    amount DOUBLE,
                    description TEXT,
                    type VARCHAR(50),
                    created_at DATETIME,
                    created_by VARCHAR(100)
                )
            """)
            db_manager.execute_non_query("""
                CREATE TABLE IF NOT EXISTS conta_income (
                    sync_id VARCHAR(50) PRIMARY KEY,
                    date VARCHAR(20),
                    amount DOUBLE,
                    description TEXT,
                    source VARCHAR(100),
                    created_at DATETIME,
                    created_by VARCHAR(100)
                )
            """)
        except Exception as e:
            print(f"[MotorConta] Error creando esquema en MariaDB: {e}")

        # 2. Esquema en SQLite (Local)
        try:
            with self.db_conta.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(expenses)")
                cols = [col[1] for col in cursor.fetchall()]
                if 'sync_id' not in cols:
                    cursor.execute("ALTER TABLE expenses ADD COLUMN sync_id TEXT")
                if 'synced' not in cols:
                    cursor.execute("ALTER TABLE expenses ADD COLUMN synced INTEGER DEFAULT 0")

                cursor.execute("PRAGMA table_info(income)")
                cols_inc = [col[1] for col in cursor.fetchall()]
                if 'sync_id' not in cols_inc:
                    cursor.execute("ALTER TABLE income ADD COLUMN sync_id TEXT")
                if 'synced' not in cols_inc:
                    cursor.execute("ALTER TABLE income ADD COLUMN synced INTEGER DEFAULT 0")

                # Asignar sync_id a los que no tienen
                cursor.execute("SELECT id FROM expenses WHERE sync_id IS NULL")
                for row in cursor.fetchall():
                    cursor.execute("UPDATE expenses SET sync_id = ?, synced = 0 WHERE id = ?", (str(uuid.uuid4()), row[0]))
                
                cursor.execute("SELECT id FROM income WHERE sync_id IS NULL")
                for row in cursor.fetchall():
                    cursor.execute("UPDATE income SET sync_id = ?, synced = 0 WHERE id = ?", (str(uuid.uuid4()), row[0]))
                
                conn.commit()
        except Exception as e:
            print(f"[MotorConta] Error adaptando esquema SQLite: {e}")

    def run(self):
        while self.running:
            time.sleep(10)
            try:
                # Verificar conexiÃ³n a Maestra
                if not db_manager.get_connection():
                    continue

                
                # Sincronizar ventas automaticamente (TPV -> Contabilidad)
                try:
                    from src.contabilidad.integracion_maestra.sincronizador import SincronizadorMaestra
                    sinc = SincronizadorMaestra(self.db_conta)
                    
                    # ENTERPRISE: Usar sincronizaciÃ³n con detalle si el modo estÃ¡ activo
                    if self.db_conta.is_enterprise_mode():
                        # Genera asientos contables y comprobantes fiscales automÃ¡ticamente
                        if sinc.traer_ventas_con_detalle_enterprise():
                            print('[MotorConta] SincronizaciÃ³n enterprise completada con asientos y comprobantes')
                    else:
                        # Modo legacy normal
                        if sinc.traer_ventas_del_dia():
                            pass
                except Exception as e:
                    print(f'[MotorConta] Error importando ventas auto: {e}')

                self._asegurar_esquemas()

                pushed = 0
                pulled = 0

                # PUSH Expenses
                with self.db_conta.get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM expenses WHERE synced = 0 OR synced IS NULL")
                    unsynced_exp = cursor.fetchall()
                
                for exp in unsynced_exp:
                    try:
                        db_manager.execute_non_query(
                            "INSERT IGNORE INTO conta_expenses (sync_id, date, category, amount, description, type, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (exp['sync_id'], exp['date'], exp['category'], exp['amount'], exp['description'], exp['type'], exp.get('created_at'), exp.get('created_by'))
                        )
                        with self.db_conta.get_connection() as conn:
                            conn.execute("UPDATE expenses SET synced = 1 WHERE sync_id = ?", (exp['sync_id'],))
                        pushed += 1
                    except Exception as e:
                        print(f"Error push exp: {e}")

                # PUSH Income
                with self.db_conta.get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM income WHERE synced = 0 OR synced IS NULL")
                    unsynced_inc = cursor.fetchall()
                
                for inc in unsynced_inc:
                    try:
                        db_manager.execute_non_query(
                            "INSERT IGNORE INTO conta_income (sync_id, date, amount, description, source, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (inc['sync_id'], inc['date'], inc['amount'], inc['description'], inc['source'], inc.get('created_at'), inc.get('created_by'))
                        )
                        with self.db_conta.get_connection() as conn:
                            conn.execute("UPDATE income SET synced = 1 WHERE sync_id = ?", (inc['sync_id'],))
                        pushed += 1
                    except Exception as e:
                        print(f"Error push inc: {e}")

                # PULL Expenses
                # Get all sync_ids from MariaDB
                master_exps = db_manager.execute_query("SELECT * FROM conta_expenses") or []
                with self.db_conta.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT sync_id FROM expenses")
                    local_exp_ids = {r[0] for r in cursor.fetchall() if r[0]}
                
                for me in master_exps:
                    if me.get('sync_id') not in local_exp_ids:
                        with self.db_conta.get_connection() as conn:
                            conn.execute(
                                "INSERT INTO expenses (date, category, amount, description, type, created_at, created_by, sync_id, synced) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
                                (me.get('date'), me.get('category'), me.get('amount'), me.get('description'), me.get('type'), me.get('created_at'), me.get('created_by'), me.get('sync_id'))
                            )
                        pulled += 1

                # PULL Income
                master_incs = db_manager.execute_query("SELECT * FROM conta_income") or []
                with self.db_conta.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT sync_id FROM income")
                    local_inc_ids = {r[0] for r in cursor.fetchall() if r[0]}
                
                for mi in master_incs:
                    if mi.get('sync_id') not in local_inc_ids:
                        with self.db_conta.get_connection() as conn:
                            conn.execute(
                                "INSERT INTO income (date, amount, description, source, created_at, created_by, sync_id, synced) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                                (mi.get('date'), mi.get('amount'), mi.get('description'), mi.get('source'), mi.get('created_at'), mi.get('created_by'), mi.get('sync_id'))
                            )
                        pulled += 1

                if pushed > 0 or pulled > 0:
                    self.sync_finished.emit(pushed, pulled)

            except Exception as e:
                print(f"[MotorConta] Loop error: {e}")
                self.sync_error.emit(str(e))
                time.sleep(30)
            time.sleep(30) # Check every 30s + 10s = 40s

    def stop(self):
        self.running = False
        self.wait()

