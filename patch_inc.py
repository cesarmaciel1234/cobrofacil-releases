import re, datetime
file_path = 'src/contabilidad/database.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

inc_pattern = r'def get_income\(self, month=None, year=None\):(.*?)period_str = f"\{year\}-\{month:02d\}"(.*?)query = "SELECT'
def inc_repl(match):
    return '''def get_income(self, desde=None, hasta=None, month=None, year=None):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if desde is None and hasta is None:
                if not month or not year:
                    today = datetime.date.today()
                    month, year = today.month, today.year
                period_str = f"{year}-{month:02d}-%"
                date_filter = "date LIKE ?"
                params = (period_str,)
            else:
                date_filter = "date BETWEEN ? AND ?"
                params = (desde, hasta)

            query = "SELECT'''

text = re.sub(inc_pattern, inc_repl, text, flags=re.DOTALL)
text = text.replace('WHERE date LIKE ?"', 'WHERE {date_filter}"')
text = text.replace('cursor.execute(query, (f"{period_str}-%",))', 'cursor.execute(query.format(date_filter=date_filter), params)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/contabilidad/vista_ingresos.py', 'r', encoding='utf-8') as f:
    vi = f.read()

vi = vi.replace('self._db.get_income(self._mes, self._ao)', 'self._db.get_income(self.parent()._desde, self.parent()._hasta)')
vi = vi.replace('self._db.get_income(self._mes, self._año)', 'self._db.get_income(self.parent()._desde, self.parent()._hasta)')

with open('src/contabilidad/vista_ingresos.py', 'w', encoding='utf-8') as f:
    f.write(vi)

with open('src/contabilidad/vista_gastos.py', 'r', encoding='utf-8') as f:
    vg = f.read()
# Note: get_expenses does not receive month/year, wait, let me check how get_expenses is called in vista_gastos.py!
print("Done")
