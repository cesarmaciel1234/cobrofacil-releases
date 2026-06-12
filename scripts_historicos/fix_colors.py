import os
import re

admin_dir = os.path.join('src', 'admin')

for filename in os.listdir(admin_dir):
    if not filename.endswith('.py'): continue
    filepath = os.path.join(admin_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    changed = False
    for i, line in enumerate(lines):
        # find " color: white" or "color: white"
        if re.search(r'(?<!-)color:\s*(?:white|#fff|#ffffff)', line, re.IGNORECASE):
            # check if it already has a dark background
            if re.search(r'background(?:-color)?:\s*(?!white|transparent|rgba\(\d+,\s*\d+,\s*\d+,\s*0(?:\.0)?\))', line, re.IGNORECASE):
                # Has a background that is not white or transparent, so white text is fine
                pass
            else:
                # Needs fixing!
                if 'btn' in line.lower() or 'qpushbutton' in line.lower() or 'button' in line.lower():
                    # It's a button, let's give it a blue background
                    line = re.sub(r'color:\s*white;?', r'background-color: #3b82f6; color: white;', line, flags=re.IGNORECASE)
                    # if it had background: white, remove it
                    line = re.sub(r'background(?:-color)?:\s*white;?', '', line, flags=re.IGNORECASE)
                    changed = True
                elif 'header' in line.lower() or 'title' in line.lower() or 'lbl' in line.lower() or 'label' in line.lower():
                    if 'estado' in line.lower() or 'semaforo' in line.lower():
                        # Let it keep white text but give it a neutral dark background if none exists
                        line = re.sub(r'color:\s*white;?', r'background-color: #64748b; color: white;', line, flags=re.IGNORECASE)
                    else:
                        # Headers/titles can be blue or dark. Let's make them dark slate so they look like headers
                        line = re.sub(r'color:\s*white;?', r'background-color: #1e293b; color: white;', line, flags=re.IGNORECASE)
                    line = re.sub(r'background(?:-color)?:\s*white;?', '', line, flags=re.IGNORECASE)
                    changed = True
                else:
                    # Generic input, table, or unknown. Change text to dark slate
                    line = re.sub(r'color:\s*white;?', r'color: #1e293b;', line, flags=re.IGNORECASE)
                    changed = True
                
                lines[i] = line

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Fixed {filename}")

print("Done")
