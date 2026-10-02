import re

file_path = 'src/contabilidad/vista_gastos.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'all_exp = self\._db\.get_expenses\(\)(.*?)period  = f"\{self\._a[oñ]+}-\{self\._mes:02d\}"(.*?)rows    = \[r for r in \(all_exp or \[\]\) if str\(r\[1\] or ""\)\.startswith\(period\)(.*?)\]'

def repl(match):
    return '''all_exp = self._db.get_expenses()
            desde = self.parent()._desde
            hasta = self.parent()._hasta
            rows = []
            for r in (all_exp or []):
                fecha_str = str(r[1] or "")
                if desde and hasta:
                    if not (desde <= fecha_str <= hasta):
                        continue
                if str(r[5] or "") == 'tesoreria': continue
                rows.append(r)'''

text = re.sub(pattern, repl, text, flags=re.DOTALL)
text = text.replace('self._mes, self._año', 'None, None')
text = text.replace('self._mes, self._a\xf1o', 'None, None')
text = text.replace('self._mes, self._ao', 'None, None')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Gastos patched")
