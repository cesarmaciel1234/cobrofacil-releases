import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'(                        cell\.border = border_thin\s*)(                            cell\.font = cell_font)', text, flags=re.DOTALL)
if match:
    correct = """                        cell.border = border_thin
                        
                    for row_idx, row_vals in enumerate(self.data, 2):
                        for col_idx, val in enumerate(row_vals, 1):
                            cell_val = val
                            if col_idx in (6, 8, 9):
                                clean_val = val.replace("$", "").replace(",", "").strip()
                                try:
                                    cell_val = float(clean_val)
                                except:
                                    pass
                                    
                            cell = ws.cell(row=row_idx, column=col_idx, value=cell_val)
                            cell.font = cell_font"""
    text = text.replace(match.group(0), correct)
    codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8').write(text)
    print('Fixed excel logic.')
else:
    print('Regex failed')
