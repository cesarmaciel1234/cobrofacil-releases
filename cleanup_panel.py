import codecs
import re

path = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_der.py'
with codecs.open(path, 'r', 'utf-8', errors='ignore') as f:
    code = f.read()

# 1. Back to White Theme
white_css = '''        self.setStyleSheet(f"""
            CyberFeedItem {{
                background-color: #FFFFFF; 
                border: 1px solid #E2E8F0;
                border-left: 4px solid {color};
                border-radius: 6px; 
                margin-bottom: 6px;
            }}
            CyberFeedItem:hover {{
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-left: 6px solid {color};
            }}
        """)'''
code = re.sub(r'self\.setStyleSheet\(f\"\"\"\s*CyberFeedItem \{\s*background-color: #1E293B;.*?\"\"\"\)', white_css, code, flags=re.DOTALL)

# 2. Change time pill to be white mode
code = code.replace(
    "background-color: #0F172A; color: #94A3B8;", 
    "background-color: #F1F5F9; color: #475569;"
)
# 3. Change description text color back to dark for white mode
code = code.replace(
    "color: #94A3B8; font-size: 12px; font-style: italic;", 
    "color: #475569; font-size: 12px; font-style: italic;"
)

# 4. Remove txt_buscar and cmb_tipo_evento logic from layout_inf
# They are added to filt_bar, which is added to layout_inf.
# Let's just remove the visual components, we still need cmb_tipo_evento internally for logic!
# Actually, if we hide cmb_tipo_evento, the logic still works perfectly!
code = code.replace('filt_bar.addWidget(self.txt_buscar)', 'self.txt_buscar.hide()')
code = code.replace('filt_bar.addWidget(self.cmb_tipo_evento)', 'self.cmb_tipo_evento.hide()')
code = code.replace('layout_inf.addLayout(filt_bar)', '# layout_inf.addLayout(filt_bar) # Se oculta la barra vieja de busqueda por orden del usuario')


with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)
