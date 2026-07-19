import os

filepath = r"src\jefe\contabilidad\database.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''
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
'''

if 'def get_daily_drain' not in content:
    content = content.replace('    def get_stats(self, month=None, year=None):', new_func + '\n    def get_stats(self, month=None, year=None):')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added get_daily_drain')
