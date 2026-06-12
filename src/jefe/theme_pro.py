# src/jefe/theme_pro.py

THEME_PRO = {
    "bg":          "#F4F7FB",   # Extremely soft, slightly cool light background
    "surface":     "#FFFFFF",   # Pure white for cards
    "surface2":    "#F8FAFC",   # Slightly off-white for secondary elements
    "border":      "#E2E8F0",   # Soft slate border
    "border2":     "#CBD5E1",   # Medium slate border
    "text":        "#0F172A",   # Deep slate for primary text (almost black)
    "text2":       "#475569",   # Medium slate for secondary text
    "text3":       "#94A3B8",   # Light slate for disabled/tertiary text
    "primary":     "#6366F1",   # Vibrant Indigo
    "primary_h":   "#4F46E5",   # Darker Indigo for hover
    "success":     "#10B981",   # Vibrant Emerald
    "danger":      "#EF4444",   # Vibrant Red
    "warning":     "#F59E0B",   # Vibrant Amber
    "info":        "#0EA5E9",   # Vibrant Sky Blue
    
    # Specific elements
    "sidebar_bg":  "#FFFFFF",   # Pure white sidebar
    "sidebar_sel": "#EEF2FF",   # Very light indigo for selection
    "nav_bg":      "rgba(255, 255, 255, 0.85)", # Translucent white for glass effect
    "nav_border":  "#E2E8F0",
}

# Hex to RGB for shadows
def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
