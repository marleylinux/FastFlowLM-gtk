import os
import json
import re

CSS = """
.user-bubble {
    background-color: @accent_bg_color;
    color: @accent_fg_color;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    margin: 6px 20px 6px 80px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.assistant-bubble {
    background-color: @view_bg_color;
    color: @window_fg_color;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 16px;
    margin: 6px 80px 6px 20px;
    border: 1px solid alpha(@window_fg_color, 0.05);
}

.accent-btn {
    background-color: @accent_bg_color;
    color: @accent_fg_color;
    border: none;
}

.accent-btn:hover {
    background-color: shade(@accent_bg_color, 1.1);
}

.accent-btn:active {
    background-color: shade(@accent_bg_color, 0.9);
}

.rounded-image {
    border-radius: 12px;
}

progressbar.suggested-action > trough > progress {
    background-color: @accent_bg_color;
    border-radius: 10px;
}

.chat-scroll {
    background-color: @window_bg_color;
}

.input-area {
    padding: 16px 24px;
    background-color: transparent;
}

.input-view {
    border-radius: 24px;
    padding: 8px 16px;
    background-color: @view_bg_color;
    border: 1px solid alpha(@window_fg_color, 0.1);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.uninstalled-model-label {
    opacity: 0.5;
}

.installed-model-label {
    font-weight: 500;
}

.sidebar-title {
    font-weight: 600;
    font-size: 0.95em;
}

.sidebar-subtitle {
    opacity: 0.7;
    font-size: 0.85em;
}

.sidebar-list {
    background-color: @window_bg_color;
    border-right: 1px solid @borders;
}

.sidebar-list list {
    background-color: transparent;
}

.sidebar-list row {
    border-radius: 12px;
    margin: 2px 8px;
    transition: all 200ms ease;
}

.sidebar-list row:hover {
    background-color: alpha(@window_fg_color, 0.05);
}

.sidebar-list row:selected {
    background-color: alpha(@accent_bg_color, 0.2);
    color: @accent_bg_color;
}

.sidebar-list row:selected .sidebar-title,
.sidebar-list row:selected .sidebar-subtitle {
    color: @accent_bg_color;
}

.delete-btn {
    opacity: 0;
    transition: opacity 200ms ease;
}

row:hover .delete-btn {
    opacity: 0.6;
}

.delete-btn:hover {
    opacity: 1.0 !important;
    color: @error_color;
}
"""

def markdown_to_pango(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'```(.*?)\n?(.*?)```', r'\n<span font_family="monospace" background="#1e1e1e" color="#dcdcdc">\2</span>\n', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'<span font_family="monospace" background="#1e1e1e" color="#dcdcdc">\1</span>', text)
    return text
