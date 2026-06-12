import re

with open('src/main_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix screens list
text = text.replace(
'''            None,    # 19 — Jefe0Dashboard           (lazy)
        ]''',
'''            None,    # 19 — Jefe0Dashboard           (lazy)
            None,    # 20 — JefeReportes             (lazy)
            None,    # 21 — CarteleriaMain           (lazy)
        ]''')

# Fix factories list
# Let's find index 19 in factories and append 20 and 21
text = text.replace(
'''            19: lambda: __import__('src.jefe.jefe0_dashboard',    fromlist=['Jefe0Dashboard']).Jefe0Dashboard(),
        }''',
'''            19: lambda: __import__('src.jefe.jefe0_dashboard',    fromlist=['Jefe0Dashboard']).Jefe0Dashboard(),
            20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['ReportesMain']).ReportesMain(),
            21: lambda: __import__('src.carteleria.carteleria_main', fromlist=['CarteleriaMain']).CarteleriaMain(),
        }''')

with open('src/main_window.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed main_window.py missing indices!')
