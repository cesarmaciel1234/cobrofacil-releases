import re

# 1. Update SQLite Schema in database.py
with open('src/contabilidad/database.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r'(CREATE TABLE IF NOT EXISTS expenses \([\s\S]*?type TEXT DEFAULT \'variable\')',
    r'\1,\n                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    created_by TEXT DEFAULT \'local\'',
    text
)

text = re.sub(
    r'(CREATE TABLE IF NOT EXISTS income \([\s\S]*?source TEXT)',
    r'\1,\n                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n                    created_by TEXT DEFAULT \'local\'',
    text
)

migration_code = '''
            # Migrations for Audit fields in Contabilidad
            for table in ['expenses', 'income']:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [col[1] for col in cursor.fetchall()]
                if 'created_at' not in cols:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                if 'created_by' not in cols:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_by TEXT DEFAULT 'local'")
'''

if 'Migrations for Audit fields' not in text:
    text = text.replace('conn.commit()', migration_code + '\n            conn.commit()', 1)

with open('src/contabilidad/database.py', 'w', encoding='utf-8') as f:
    f.write(text)

# 2. Update MariaDB Schema in motor_sync_conta.py
with open('src/contabilidad/integracion_maestra/motor_sync_conta.py', 'r', encoding='utf-8') as f:
    motor_text = f.read()

motor_text = motor_text.replace(
    'type VARCHAR(50)\n                )',
    'type VARCHAR(50),\n                    created_at DATETIME,\n                    created_by VARCHAR(100)\n                )'
)

motor_text = motor_text.replace(
    'source VARCHAR(100)\n                )',
    'source VARCHAR(100),\n                    created_at DATETIME,\n                    created_by VARCHAR(100)\n                )'
)

# SQLite migrations for motor_sync_conta.py (which handles syncing)
# We don't need to add columns to sqlite here, because database.py already does it on init.
# But we need to update the PUSH and PULL queries!

motor_text = motor_text.replace(
    '"INSERT IGNORE INTO conta_expenses (sync_id, date, category, amount, description, type) VALUES (?, ?, ?, ?, ?, ?)",',
    '"INSERT IGNORE INTO conta_expenses (sync_id, date, category, amount, description, type, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",'
)
motor_text = motor_text.replace(
    "(exp['sync_id'], exp['date'], exp['category'], exp['amount'], exp['description'], exp['type'])",
    "(exp['sync_id'], exp['date'], exp['category'], exp['amount'], exp['description'], exp['type'], exp.get('created_at'), exp.get('created_by'))"
)

motor_text = motor_text.replace(
    '"INSERT IGNORE INTO conta_income (sync_id, date, amount, description, source) VALUES (?, ?, ?, ?, ?)",',
    '"INSERT IGNORE INTO conta_income (sync_id, date, amount, description, source, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",'
)
motor_text = motor_text.replace(
    "(inc['sync_id'], inc['date'], inc['amount'], inc['description'], inc['source'])",
    "(inc['sync_id'], inc['date'], inc['amount'], inc['description'], inc['source'], inc.get('created_at'), inc.get('created_by'))"
)

motor_text = motor_text.replace(
    '"INSERT INTO expenses (date, category, amount, description, type, sync_id, synced) VALUES (?, ?, ?, ?, ?, ?, 1)",',
    '"INSERT INTO expenses (date, category, amount, description, type, created_at, created_by, sync_id, synced) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",'
)
motor_text = motor_text.replace(
    "(me.get('date'), me.get('category'), me.get('amount'), me.get('description'), me.get('type'), me.get('sync_id'))",
    "(me.get('date'), me.get('category'), me.get('amount'), me.get('description'), me.get('type'), me.get('created_at'), me.get('created_by'), me.get('sync_id'))"
)

motor_text = motor_text.replace(
    '"INSERT INTO income (date, amount, description, source, sync_id, synced) VALUES (?, ?, ?, ?, ?, 1)",',
    '"INSERT INTO income (date, amount, description, source, created_at, created_by, sync_id, synced) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",'
)
motor_text = motor_text.replace(
    "(mi.get('date'), mi.get('amount'), mi.get('description'), mi.get('source'), mi.get('sync_id'))",
    "(mi.get('date'), mi.get('amount'), mi.get('description'), mi.get('source'), mi.get('created_at'), mi.get('created_by'), mi.get('sync_id'))"
)

with open('src/contabilidad/integracion_maestra/motor_sync_conta.py', 'w', encoding='utf-8') as f:
    f.write(motor_text)

print('Updated motor_sync_conta.py and database.py')
