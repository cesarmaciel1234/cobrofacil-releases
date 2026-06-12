import codecs

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_hist = False
in_audit = False

for i, line in enumerate(lines):
    # Remove the broken try blocks from previous attempt
    if line.strip() == "try:":
        continue
    if line.strip() == "finally:":
        continue
    if "self._is_loading_historial = False" in line and "finally:" not in lines[i-1]:
        continue
    if "self._is_loading_audit = False" in line and "finally:" not in lines[i-1]:
        continue
    if line.strip() == "if getattr(self, '_is_loading_historial', False): return":
        continue
    if line.strip() == "self._is_loading_historial = True":
        continue
    if line.strip() == "if getattr(self, '_is_loading_audit', False): return":
        continue
    if line.strip() == "self._is_loading_audit = True":
        continue

    new_lines.append(line)
    
    if "def _cargar_historial_pagina(self):" in line:
        new_lines.append("        if getattr(self, '_is_loading_historial', False): return\n")
        new_lines.append("        self._is_loading_historial = True\n")
        in_hist = True
    
    if "def _cargar_audit_pagina(self):" in line:
        new_lines.append("        if getattr(self, '_is_loading_audit', False): return\n")
        new_lines.append("        self._is_loading_audit = True\n")
        in_audit = True
        
    if "self.historial_offset += self.historial_limit" in line and in_hist:
        new_lines.append("        self._is_loading_historial = False\n")
        in_hist = False

    if "self.audit_offset += self.audit_limit" in line and in_audit:
        new_lines.append("        self._is_loading_audit = False\n")
        in_audit = False
        
    # Handle early returns
    if in_hist and "if not rows: return" in line:
        new_lines.pop()
        new_lines.append("        if not rows:\n")
        new_lines.append("            self._is_loading_historial = False\n")
        new_lines.append("            return\n")

    if in_audit and "if not rows: return" in line:
        new_lines.pop()
        new_lines.append("        if not rows:\n")
        new_lines.append("            self._is_loading_audit = False\n")
        new_lines.append("            return\n")

with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed")
