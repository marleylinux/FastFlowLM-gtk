#!/usr/bin/env python3
import sys
import asyncio
import json
import subprocess
import socket
import os
import signal
from typing import Optional, List, Dict

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Adw, Soup
from gi.events import GLibEventLoopPolicy

# Set the policy BEFORE creating any loops
asyncio.set_event_loop_policy(GLibEventLoopPolicy())

APP_ID = "com.marley.FlmChat"
DEFAULT_PORT = 52625
BASE_URL = f"http://127.0.0.1:{DEFAULT_PORT}/v1"

CSS = """
.chat-window {
    background-color: #000000;
}

.user-bubble {
    background-color: @accent_bg_color;
    color: @accent_fg_color;
    border-radius: 12px;
    padding: 10px 14px;
    margin: 5px 20px 5px 60px;
}

.assistant-bubble {
    background-color: #000000;
    color: @window_fg_color;
    border-radius: 12px;
    padding: 10px 14px;
    margin: 5px 60px 5px 20px;
}

.chat-scroll {
    border-bottom: 1px solid @borders;
}

.input-area {
    padding: 12px;
}
"""

class FlmChatApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.server_process: Optional[subprocess.Popen] = None
        self.models: List[Dict] = []
        self.current_model: Optional[str] = None
        self.tasks = set()
        self.session = Soup.Session()
        self.history = []
        self.status_labels = []

    def do_activate(self):
        # Force dark mode
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_default_size(600, 800)
        self.win.set_title("Just Talk")

        # Load CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # UI Layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_content(self.main_box)

        # HeaderBar
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)

        # New Chat Button
        self.btn_new = Gtk.Button(icon_name="document-new-symbolic")
        self.btn_new.set_tooltip_text("New Chat")
        self.btn_new.connect("clicked", self.on_new_chat)
        self.header.pack_start(self.btn_new)

        # Model Selector (ComboRow inside a Popover for minimalism)
        self.model_btn = Gtk.MenuButton(label="Selecting model...")
        self.header.set_title_widget(self.model_btn)
        
        # Eject Button
        self.btn_eject = Gtk.Button(icon_name="media-eject-symbolic")
        self.btn_eject.set_tooltip_text("Eject (Stop Server)")
        self.btn_eject.connect("clicked", self.on_eject)
        self.header.pack_end(self.btn_eject)

        # Chat List
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.add_css_class("chat-scroll")
        self.chat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.chat_box.set_margin_top(10)
        self.chat_box.set_margin_bottom(10)
        self.scrolled.set_child(self.chat_box)
        self.main_box.append(self.scrolled)

        # Input Area
        self.input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.input_box.add_css_class("input-area")
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Type a message...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self.on_send)
        self.input_box.append(self.entry)
        
        self.btn_send = Gtk.Button(icon_name="mail-send-symbolic")
        self.btn_send.connect("clicked", self.on_send)
        self.input_box.append(self.btn_send)
        
        self.main_box.append(self.input_box)

        self.win.present()
        
        # Start async initialization
        self.run_task(self.init_server())

    def run_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def init_server(self):
        # 1. Check if server is running
        if not self.is_server_up():
            self.add_system_message("Server not detected. Starting flm serve...")
            # Try to find a model
            models = self.get_installed_models()
            if not models:
                self.add_system_message("Error: No installed models found. Please run 'flm pull <model>' first.")
                return
            
            self.models = models
            self.current_model = models[0]['model']
            self.start_flm_serve(self.current_model)
            
            # Wait for server to come up
            for _ in range(10):
                await asyncio.sleep(1)
                if self.is_server_up():
                    break
            else:
                self.add_system_message("Error: Server failed to start.")
                return
            
            # Clear "Starting" message
            self.clear_status_labels()
        else:
            self.add_system_message("Connected to flm serve.")
            self.models = self.get_installed_models()
            # Clear connection message after a delay
            GLib.timeout_add_seconds(2, self.clear_status_labels)

        self.update_model_ui()

    def is_server_up(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', DEFAULT_PORT)) == 0

    def get_installed_models(self) -> List[Dict]:
        try:
            res = subprocess.run(["flm", "list", "--filter", "installed", "--json"], 
                               capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            return data.get("models", [])
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def start_flm_serve(self, model: str):
        self.server_process = subprocess.Popen(["flm", "serve", model], 
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL)

    def update_model_ui(self):
        # Update MenuButton label and build Popover
        if self.current_model:
            self.model_btn.set_label(self.current_model)
        
        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        
        for m in self.models:
            btn = Gtk.Button(label=m['model'])
            btn.connect("clicked", self.on_model_selected, m['model'], popover)
            vbox.append(btn)
        
        popover.set_child(vbox)
        self.model_btn.set_popover(popover)

    def on_model_selected(self, btn, model_name, popover):
        self.current_model = model_name
        self.model_btn.set_label(model_name)
        popover.popdown()
        self.add_system_message(f"Switching to model: {model_name}")
        # Note: flm serve handles dynamic loading, so we just update our internal state

    def add_message(self, text: str, is_user: bool):
        bubble = Gtk.Label(label=text)
        bubble.set_wrap(True)
        bubble.set_selectable(True)
        bubble.set_xalign(0)
        bubble.add_css_class("user-bubble" if is_user else "assistant-bubble")
        
        align = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if is_user:
            align.append(Gtk.Box(hexpand=True))
            align.append(bubble)
        else:
            align.append(bubble)
            align.append(Gtk.Box(hexpand=True))
            
        self.chat_box.append(align)
        # Scroll to bottom
        GLib.idle_add(self.scroll_to_bottom)
        return bubble

    def add_system_message(self, text: str):
        label = Gtk.Label(label=text)
        label.add_css_class("dim-label")
        label.set_margin_top(10)
        label.set_margin_bottom(10)
        self.chat_box.append(label)
        self.status_labels.append(label)
        GLib.idle_add(self.scroll_to_bottom)

    def clear_status_labels(self):
        for label in self.status_labels:
            if label.get_parent() == self.chat_box:
                self.chat_box.remove(label)
        self.status_labels = []
        return False # For timeout_add compatibility

    def scroll_to_bottom(self):
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def on_new_chat(self, btn):
        child = self.chat_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.chat_box.remove(child)
            child = next_child
        self.history = []
        self.add_system_message("New session started.")

    def on_eject(self, btn):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            self.add_system_message("Server stopped.")
        else:
            # Try to kill any existing flm process
            subprocess.run(["pkill", "-f", "flm serve"])
            self.add_system_message("Ejected any active server.")

    def on_send(self, widget):
        text = self.entry.get_text().strip()
        if not text:
            return
        self.entry.set_text("")
        self.add_message(text, is_user=True)
        self.history.append({"role": "user", "content": text})
        self.run_task(self.get_ai_response())

    async def get_ai_response(self):
        if not self.current_model:
            self.add_system_message("No model selected.")
            return

        bubble = self.add_message("", is_user=False)
        full_content = ""
        
        payload = {
            "model": self.current_model,
            "messages": self.history,
            "stream": True
        }
        
        msg = Soup.Message.new("POST", f"{BASE_URL}/chat/completions")
        msg.set_request_body_from_bytes("application/json", GLib.Bytes.new(json.dumps(payload).encode()))
        
        try:
            # Soup 3 send_async expects (msg, priority, cancellable) when used as awaitable
            stream = await self.session.send_async(msg, GLib.PRIORITY_DEFAULT, None)
            if not stream:
                self.add_system_message(f"Error: Server returned empty stream (Status: {msg.get_status()})")
                return
                
            data_stream = Gio.DataInputStream.new(stream)
            
            while True:
                # Read line-by-line for SSE
                line_bytes, length = await data_stream.read_line_async(GLib.PRIORITY_DEFAULT, None)
                if line_bytes is None: # EOF
                    break
                
                line = line_bytes.decode('utf-8').strip()
                if not line:
                    continue
                    
                if line.startswith("data: "):
                    content = line[6:]
                    if content == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(content)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                text = delta['content']
                                if text is not None:
                                    full_content += text
                                    bubble.set_label(full_content)
                                    self.scroll_to_bottom()
                    except Exception as e:
                        print(f"Error parsing chunk: {e}")
            
            self.history.append({"role": "assistant", "content": full_content})
            
        except Exception as e:
            self.add_system_message(f"Connection error: {str(e)}")

    def do_shutdown(self):
        if self.server_process:
            self.server_process.terminate()
        # Ensure we chain up to the parent class correctly
        Adw.Application.do_shutdown(self)

if __name__ == "__main__":
    app = FlmChatApp()
    app.run(sys.argv)
