import os
import re

STRUCTURAL_PROPS = {
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'font-size', 'font-family', 'font-weight', 'text-align', 'letter-spacing',
    'border-radius', 'border-top-left-radius', 'border-top-right-radius',
    'border-bottom-left-radius', 'border-bottom-right-radius',
    'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
    'spacing', 'qproperty-alignment'
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    base_content = []
    theme_content = []
    
    # We will parse block by block
    # A block is everything up to }
    
    parts = re.split(r'(\})', content)
    
    for i in range(0, len(parts)-1, 2):
        block = parts[i]
        brace = parts[i+1]
        
        if '{' not in block:
            # It might be just trailing whitespace or comments at the end
            theme_content.append(block + brace)
            continue
            
        header, body = block.split('{', 1)
        
        base_body_lines = []
        theme_body_lines = []
        
        lines = body.split('\n')
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('/*'):
                theme_body_lines.append(line)
                continue
                
            # Check if it's a structural property
            is_struct = False
            for p in STRUCTURAL_PROPS:
                if stripped.startswith(p + ':') or stripped.startswith(p + ' :'):
                    is_struct = True
                    break
            
            # Special case for border: none; or border: 1px solid #ccc;
            # We don't extract border colors, so we leave borders in theme unless it's just border: none;
            if stripped.startswith('border:') and 'none' in stripped:
                is_struct = True
                
            if is_struct:
                base_body_lines.append(line)
            else:
                theme_body_lines.append(line)
                
        # Reconstruct
        if base_body_lines:
            base_content.append(header + "{\n" + "\n".join(base_body_lines) + "\n}")
        
        if theme_body_lines:
            # Only add if there's actual CSS props left, or comments
            has_props = any(':' in l for l in theme_body_lines)
            if has_props or header.strip().startswith('/*'):
                theme_content.append(header + "{" + "\n".join(theme_body_lines) + "}")
            else:
                # If only comments left in body but no props, we might still want to keep it or discard.
                theme_content.append(header + "{" + "\n".join(theme_body_lines) + "}")
        
    return "\n".join(base_content), "\n".join(theme_content)

d_base, d_theme = process_file('src/ui_components/estilo_dia.qss')
n_base, n_theme = process_file('src/ui_components/estilo_noche.qss')

# base.qss will just be d_base (since both should be identical structurally)
with open('src/ui_components/base.qss', 'w', encoding='utf-8') as f:
    f.write("/* BASE STRUCTURAL STYLES */\n" + d_base)

with open('src/ui_components/estilo_dia.qss', 'w', encoding='utf-8') as f:
    f.write(d_theme)

with open('src/ui_components/estilo_noche.qss', 'w', encoding='utf-8') as f:
    f.write(n_theme)

print("Refactoring complete.")
