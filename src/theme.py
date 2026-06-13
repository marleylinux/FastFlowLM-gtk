# theme
import os
import json
import utils

# palettes
THEME_PALETTES = {
    "default": {
        "accent": "#3584e4", # Adwaita Blue
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#30d158", "installed_bg": "rgba(48, 209, 88, 0.12)",
        "vlm_fg": "#ab47bc", "vlm_bg": "rgba(171, 71, 188, 0.12)",
        "download_fg": "#f5c211", "download_bg": "rgba(245, 194, 17, 0.12)"
    },
    "ryzen": {
        "accent": "#ff3b30", # Luminous Red
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#ff9f0a", "installed_bg": "rgba(255, 159, 10, 0.12)",
        "vlm_fg": "#bf5af2", "vlm_bg": "rgba(191, 90, 242, 0.12)",
        "download_fg": "#ffd60a", "download_bg": "rgba(255, 214, 10, 0.12)"
    },
    "geforce": {
        "accent": "#76ff03", # Electric Lime
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#00e5ff", "installed_bg": "rgba(0, 229, 255, 0.12)",
        "vlm_fg": "#ff4081", "vlm_bg": "rgba(255, 64, 129, 0.12)",
        "download_fg": "#ffd60a", "download_bg": "rgba(255, 214, 10, 0.12)"
    },
    "intel": {
        "accent": "#0071e3", # Intel Luminous Blue
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#30d158", "installed_bg": "rgba(48, 209, 88, 0.12)",
        "vlm_fg": "#ff9f0a", "vlm_bg": "rgba(255, 159, 10, 0.12)",
        "download_fg": "#ffea00", "download_bg": "rgba(255, 234, 0, 0.12)"
    },
    "arch": {
        "accent": "#1793d1", # Arch Blue
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#ffd60a", "installed_bg": "rgba(255, 214, 10, 0.12)",
        "vlm_fg": "#bf5af2", "vlm_bg": "rgba(191, 90, 242, 0.12)",
        "download_fg": "#ff9f0a", "download_bg": "rgba(255, 159, 10, 0.12)"
    },
    "saints": {
        "accent": "#af52de", # Saints Purple
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#5eebff", "installed_bg": "rgba(94, 235, 255, 0.12)",
        "vlm_fg": "#ff3700", "vlm_bg": "rgba(255, 55, 0, 0.12)",
        "download_fg": "#ffd60a", "download_bg": "rgba(255, 214, 10, 0.12)"
    },
    "noctua": {
        "accent": "#9c6644", # Noctua Brown
        "sidebar_bg": "@sidebar_bg_color",
        "installed_fg": "#a8dadc", "installed_bg": "rgba(168, 218, 220, 0.12)",
        "vlm_fg": "#e63946", "vlm_bg": "rgba(230, 57, 70, 0.12)",
        "download_fg": "#ffd60a", "download_bg": "rgba(255, 214, 10, 0.12)"
    }
}

def load_theme_name() -> str:
    # load theme name
    config_path = os.path.expanduser("~/.config/flm/theme.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f).get("theme_name", "default")
        except Exception:
            pass
    return "default"

def apply_theme(app, theme_name: str) -> None:
    # Get palette or fallback to default
    palette = THEME_PALETTES.get(theme_name, THEME_PALETTES["default"])
    accent = palette["accent"]
    sidebar_bg = palette["sidebar_bg"]
    
    css_lines = []
    if theme_name != "default":
        css_lines.append(f"@define-color accent_color {accent};")
        css_lines.append(f"@define-color accent_bg_color {accent};")
        css_lines.append("@define-color accent_fg_color #ffffff;")
        css_lines.append(f"@define-color suggested_bg_color {accent};")
        css_lines.append("@define-color suggested_fg_color #ffffff;")
        css_lines.append(f"@define-color selection_bg_color {accent};")
        css_lines.append("@define-color selection_fg_color #ffffff;")
        
        # Explicit overrides for buttons and entries to force them to use the accent
        css_lines.append(".suggested-action { background-color: @accent_bg_color; color: @accent_fg_color; }")
        css_lines.append(".accent-btn { background-color: @accent_bg_color; color: @accent_fg_color; }")
        css_lines.append("selection { background-color: @accent_bg_color; color: @accent_fg_color; }")
    else:
        # For default, use standard Adwaita blue
        css_lines.append("@define-color accent_bg_color #3584e4;")

    # Inject dynamic sidebar and badge colors
    if sidebar_bg != "@sidebar_bg_color":
        css_lines.append(f"@define-color sidebar_bg_color {sidebar_bg};")
    css_lines.append(f"@define-color installed_badge_fg {palette['installed_fg']};")
    css_lines.append(f"@define-color installed_badge_bg {palette['installed_bg']};")
    css_lines.append(f"@define-color vlm_badge_fg {palette['vlm_fg']};")
    css_lines.append(f"@define-color vlm_badge_bg {palette['vlm_bg']};")
    css_lines.append(f"@define-color download_badge_fg {palette['download_fg']};")
    css_lines.append(f"@define-color download_badge_bg {palette['download_bg']};")

    # append standard css
    full_css = "\n".join(css_lines) + "\n" + utils.CSS
    app.css_provider.load_from_data(full_css.encode())
