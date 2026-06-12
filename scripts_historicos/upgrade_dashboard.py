import codecs
import re

text = codecs.open('src/jefe/jefe0_dashboard.py', 'r', encoding='utf-8').read()

# Replace palette import and usage
text = text.replace('L = {', 'from src.jefe.theme_pro import THEME_PRO as L\n# L = {')

# Adjust the JEFE_MODULES to have dark backgrounds
modules_replacement = '''JEFE_MODULES = [
    ("reportes",     "Reportes\\ny Ventas",       "📊", "#10B981", "#022C22", "#D1FAE5", 20,  None),
    ("nexus_pro",    "Nexus Pro\\nControl",        "🌌", "#6366F1", "#1E1B4B", "#E0E7FF", 18, None),
    ("contabilidad", "Contabilidad\\nERP",         "💹", "#F59E0B", "#451A03", "#FEF3C7", 9,  None),
    ("proveedores",  "Proveedores\\nERP",          "🚚", "#0EA5E9", "#082F49", "#E0F2FE", 9,  3),
]'''
text = re.sub(r'JEFE_MODULES = \[.*?\]', modules_replacement, text, flags=re.DOTALL)

# Adjust Hero gradient
hero_replacement = '''QFrame#JefeHero {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0.00 #1E1B4B,
                    stop:0.45 #312E81,
                    stop:0.80 #064E3B,
                    stop:1.00 #065F46
                );
                border-radius: 18px;
                border: 1px solid #374151;
            }'''
text = re.sub(r'QFrame#JefeHero \{.*?\}', hero_replacement, text, flags=re.DOTALL)

# Adjust brand text color and buttons for Dark Mode
text = text.replace("color:#1E293B;", "color:#F8FAFC;")
text = text.replace("background: #F1F5F9; color: #475569;", "background: #1E293B; color: #F8FAFC;")
text = text.replace("border: 1.5px solid #E2E8F0;", "border: 1px solid #334155;")
text = text.replace("background: #E0F2FE; color: #0284C7; border-color: #BAE6FD;", "background: #0284C7; color: #FFFFFF; border-color: #38BDF8;")
text = text.replace("background: #FEE2E2; color: #EF4444; border-color: #FECACA;", "background: #7F1D1D; color: #FFFFFF; border-color: #EF4444;")

codecs.open('src/jefe/jefe0_dashboard.py', 'w', encoding='utf-8').write(text)
print('Dashboard updated to PRO!')
