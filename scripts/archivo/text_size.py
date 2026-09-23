import codecs

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# In _update_search_colors (Selected state)
code = code.replace(
    'lbl_n.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: white;")',
    'lbl_n.setStyleSheet("font-size: 26px; font-weight: 900; background: transparent; color: white;")'
)
code = code.replace(
    'lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: white;")',
    'lbl_p.setStyleSheet("font-size: 22px; font-weight: bold; background: transparent; color: white;")'
)
code = code.replace(
    'lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent; color: #E2E8F0;")',
    'lbl_s.setStyleSheet("font-size: 18px; font-weight: normal; background: transparent; color: #E2E8F0;")'
)

# In _update_search_colors (Normal state)
code = code.replace(
    'lbl_n.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #0F172A;")',
    'lbl_n.setStyleSheet("font-size: 26px; font-weight: 900; background: transparent; color: #0F172A;")'
)
code = code.replace(
    'lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #059669;")',
    'lbl_p.setStyleSheet("font-size: 22px; font-weight: bold; background: transparent; color: #059669;")'
)
code = code.replace(
    'lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent; color: #64748B;")',
    'lbl_s.setStyleSheet("font-size: 18px; font-weight: normal; background: transparent; color: #64748B;")'
)

# In _do_busqueda (Creation time)
code = code.replace(
    'lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669; background: transparent;")',
    'lbl_p.setStyleSheet("font-size: 22px; font-weight: bold; background: transparent; color: #059669;")'
)
code = code.replace(
    'lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; color: #64748B; background: transparent;")',
    'lbl_s.setStyleSheet("font-size: 18px; font-weight: normal; background: transparent; color: #64748B;")'
)

# Also let's increase the height of the item widget to accommodate the huge 26px font
code = code.replace(
    'w.setMinimumHeight(60)',
    'w.setMinimumHeight(75)'
)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Typography upgraded!")
