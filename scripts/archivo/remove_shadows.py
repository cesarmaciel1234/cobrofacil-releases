import os
import re

def remove_shadows(directory):
    count = 0
    pattern_import = re.compile(r'from PyQt6\.QtWidgets import.*QGraphicsDropShadowEffect.*\n')
    pattern_shadow_inst = re.compile(r'\s*shadow\d*\s*=\s*QGraphicsDropShadowEffect\(.*?\)\s*\n')
    pattern_shadow_props = re.compile(r'\s*shadow\d*\.set.*?\n')
    pattern_set_effect = re.compile(r'\s*\w+\.setGraphicsEffect\(shadow\d*\)\s*\n')

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                orig_content = content
                
                # We need to be careful with imports. If it's the only import, remove the line.
                # If there are multiple, just remove QGraphicsDropShadowEffect,
                content = re.sub(r',\s*QGraphicsDropShadowEffect', '', content)
                content = re.sub(r'QGraphicsDropShadowEffect,\s*', '', content)
                content = re.sub(r'from PyQt6\.QtWidgets import QGraphicsDropShadowEffect\n', '', content)
                
                # Remove shadow instantiations and property sets
                content = pattern_shadow_inst.sub('', content)
                content = pattern_shadow_props.sub('', content)
                content = pattern_set_effect.sub('', content)

                if content != orig_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed {filepath}")
                    count += 1
    return count

print("Fixed:", remove_shadows("src"))
