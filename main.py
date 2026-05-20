import asyncio
import json
import subprocess
import os
import signal
import fcntl
import time
import gi
import logging
from typing import Optional, List, Dict

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Adw, Soup

import utils
import flm
import ui
import sessions
import network
import theme
import handlers
import models
import display

APP_ID = "com.marley.FastFlowLM-gtk"
DEFAULT_PORT = 52625
BASE_URL = f"http://127.0.0.1:{DEFAULT_PORT}/v1"

class FlmChatApp(Adw.Application):
    """
    Main application controller for FastFlowLM-gtk.
    Manages application state, lifecycle, and coordinates between UI/data modules.
    """
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.server_process: Optional[subprocess.Popen] = None
        self.css_provider = Gtk.CssProvider()
        self.ai_task: Optional[asyncio.Task] = None
        self.theme_color: str = theme.load_theme_color()
        self.models: List[Dict] = flm.get_all_models()
        self.current_model: Optional[str] = None
        self.utils = utils

        self.downloading_models = set()
        self.tasks = set()
        self.session = Soup.Session()
        self.history = []
        self.status_labels = []
        self.selected_image_path: Optional[str] = None
        
        self.history_dir = os.path.expanduser("~/.config/flm/history")
        os.makedirs(self.history_dir, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.sessions_metadata = []
        self.allow_mid_chat_switch = False
        self.is_sending = False
        
        self.lock_fd = None
        self.acquire_system_lock()

    def acquire_system_lock(self) -> None:
        """Acquires a file lock to manage system model resource usage."""
        lock_path = os.path.expanduser("~/.config/flm/model_ram.lock")
        try:
            self.lock_fd = open(lock_path, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, IOError):
            print("Warning: Another instance is managing the system models.")

    def do_activate(self) -> None:
        """Initializes the main window and UI components."""
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        
        # Populate models first before any UI logic
        self.models = flm.get_all_models()
        
        action_switch = Gio.SimpleAction.new_stateful("allow_switch", None, GLib.Variant.new_boolean(False))
        action_switch.connect("activate", self.on_allow_switch_toggled)
        self.add_action(action_switch)

        action_clear = Gio.SimpleAction.new("clear_history", None)
        action_clear.connect("activate", self.on_clear_history)
        self.add_action(action_clear)

        action_color = Gio.SimpleAction.new("choose_color", None)
        action_color.connect("activate", self.on_choose_color)
        self.add_action(action_color)

        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_default_size(900, 800)
        self.win.set_title("FastFlowLM-gtk")
        
        self.css_provider.load_from_data(utils.CSS.encode())
        theme.apply_theme(self, self.theme_color)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


        self.split_view = Adw.OverlaySplitView()
        self.split_view.set_sidebar_width_fraction(0.3)
        self.split_view.set_min_sidebar_width(200)
        self.win.set_content(self.split_view)

        self.sidebar_box = ui.build_sidebar(self)
        self.split_view.set_sidebar(self.sidebar_box)

        self.main_box = ui.build_main_content(self)
        self.split_view.set_content(self.main_box)

        # Ensure initial state is set before the window appears
        self.update_model_ui()
        self.show_welcome_message()

        self.win.present()
        
        # Apply theme after window is present
        theme.apply_theme(self, self.theme_color)
        
        GLib.idle_add(self.load_history_metadata)
        GLib.idle_add(lambda: self.run_task(self.init_server()))

    def on_search_changed(self, entry):
        text = entry.get_text().lower()
        
        for i, row in enumerate(self.history_list):
            session_id = self.sessions_metadata[i]["id"]
            path = os.path.join(self.history_dir, f"{session_id}.json")
            
            # Row(ListBoxRow) -> Box(main_box) -> Box(txt_box)
            main_box = row.get_child()
            txt_box = main_box.get_first_child()
            # Title is first, model subtitle is second in txt_box
            title_label = txt_box.get_first_child()
            model_label = title_label.get_next_sibling()
            
            if not text:
                row.set_visible(True)
                model_label.set_label(self.sessions_metadata[i]["model"])
                continue
                
            found_text = None
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for msg in data.get("messages", []):
                        content = msg.get("content", "")
                        if text in content.lower():
                            # Extract preview: start from match and take 40 chars, no leading '...'
                            start_idx = content.lower().find(text)
                            preview = content[start_idx:start_idx+40]
                            found_text = f"{preview}..."
                            break
            except:
                pass
            
            if found_text:
                row.set_visible(True)
                model_label.set_label(found_text)
            else:
                row.set_visible(False)

    def on_attach_clicked(self, btn):
        self.btn_attach.set_sensitive(False)
        dialog = Gtk.FileChooserNative.new("Select Image", self.win, Gtk.FileChooserAction.OPEN, "Open", "Cancel")
        filter = Gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/webp")
        dialog.add_filter(filter)
        dialog.connect("response", self.on_file_selected)
        dialog.show()

    def on_file_selected(self, dialog, response):
        self.btn_attach.set_sensitive(self.is_current_model_capable())
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            path = file.get_path()
            if path:
                self.selected_image_path = path
                self.update_thumbnail()
        dialog.destroy()

    def update_thumbnail(self):
        return display.update_thumbnail(self)

    def on_remove_thumbnail(self, btn):
        return display.on_remove_thumbnail(self)

    def on_allow_switch_toggled(self, action, value):
        new_state = not action.get_state().get_boolean()
        
        if new_state:
            dialog = Adw.MessageDialog(
                transient_for=self.win,
                heading="Enable Model Switching?",
                body="Enabling model switching allows you to change the active model at any time, which may reload the model server. Continue?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("enable", "Enable")
            dialog.set_response_appearance("enable", Adw.ResponseAppearance.SUGGESTED)
            dialog.connect("response", lambda d, r: self.complete_switch_toggle(action, r))
            dialog.present()
        else:
            self.complete_switch_toggle(action, "enable")

    def complete_switch_toggle(self, action, response):
        if response == "enable":
            new_state = not action.get_state().get_boolean()
            action.set_state(GLib.Variant.new_boolean(new_state))
            self.allow_mid_chat_switch = new_state
            self.update_model_ui()

    def run_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def init_server(self):
        self.models = flm.get_all_models()
        self.update_model_ui()

    def is_current_model_capable(self) -> bool:
        return self.is_current_model_vlm()

    def is_current_model_vlm(self) -> bool:
        if not self.current_model: return False
        model_data = next((m for m in self.models if m["model"] == self.current_model), None)
        return model_data is not None and model_data.get("vlm", False)

    def update_model_ui(self):
        models.update_model_ui(self)

    def on_row_activated(self, listbox, row, popover):
        return models.on_row_activated(self, listbox, row, popover)

    def on_model_selected(self, btn, model_data, popover):
        return models.on_model_selected(self, btn, model_data, popover)

    def init_server(self):
        return models.init_server(self)

    def wait_for_server(self):
        return models.wait_for_server(self)

    def confirm_download(self, model_data):
        return models.confirm_download(self, model_data)

    def on_download_response(self, dialog, response, model_name):
        return models.on_download_response(self, dialog, response, model_name)

    def download_model(self, model_name):
        return models.download_model(self, model_name)

    def add_message(self, text: str, is_user: bool, image_path: Optional[str] = None):
        return display.add_message(self, text, is_user, image_path)

    def add_system_message(self, text: str):
        return display.add_system_message(self, text)

    def clear_status_labels(self):
        return display.clear_status_labels(self)

    def scroll_to_bottom(self):
        return display.scroll_to_bottom(self)

    def load_history_metadata(self):
        self.sessions_metadata = []
        try:
            if not os.path.exists(self.history_dir):
                return
            files = [f for f in os.listdir(self.history_dir) if f.endswith(".json")]
            files.sort(reverse=True)
            for f in files:
                path = os.path.join(self.history_dir, f)
                with open(path, 'r') as jf:
                    data = json.load(jf)
                    self.sessions_metadata.append({
                        "id": data.get("id", f.replace(".json", "")),
                        "title": data.get("title", "Untitled Chat"),
                        "model": data.get("model", "unknown")
                    })
        except Exception as e:
            print(f"Error loading history: {e}")
        self.update_history_ui()

    def update_history_ui(self):
        child = self.history_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.history_list.remove(child)
            child = next_child
        
        for meta in self.sessions_metadata:
            row = Gtk.ListBoxRow()
            main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            main_box.set_margin_start(10)
            main_box.set_margin_end(5)
            main_box.set_margin_top(10)
            main_box.set_margin_bottom(10)
            
            txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            txt_box.set_hexpand(True)
            
            title = Gtk.Label(label=meta["title"])
            title.set_halign(Gtk.Align.START)
            title.set_ellipsize(3)
            title.set_max_width_chars(20)
            title.add_css_class("sidebar-title")
            
            model_label = meta["model"]
            model_data = next((m for m in self.models if m['model'] == meta["model"]), None)
            if model_data and model_data.get('vlm', False):
                model_label = "👁 " + model_label
            
            model = Gtk.Label(label=model_label)
            model.set_halign(Gtk.Align.START)
            model.add_css_class("sidebar-subtitle")
            
            txt_box.append(title)
            txt_box.append(model)
            main_box.append(txt_box)
            
            del_btn = Gtk.Button(icon_name="user-trash-symbolic")
            del_btn.add_css_class("delete-btn")
            del_btn.set_has_frame(False)
            del_btn.set_tooltip_text("Delete Chat")
            del_btn.connect("clicked", self.on_delete_clicked, meta["id"])
            main_box.append(del_btn)
            
            row.set_child(main_box)
            self.history_list.append(row)

    def on_delete_clicked(self, btn, session_id):
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Delete Chat?",
            body="Are you sure you want to permanently delete this conversation?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
         
        dialog.connect("response", self.on_delete_response, session_id)
        dialog.present()

    def on_delete_response(self, dialog, response, session_id):
        if response == "delete":
            path = os.path.join(self.history_dir, f"{session_id}.json")
            if os.path.exists(path):
                os.remove(path)
            
            self.sessions_metadata = [m for m in self.sessions_metadata if m["id"] != session_id]
            
            if self.current_session_id == session_id:
                self.entry.get_buffer().set_text("")
                self.chat_box_remove_all()
                self.history = []
                self.current_session_id = None
                self.update_model_ui()
                self.add_system_message("Session deleted.")
            
            self.update_history_ui()
        dialog.destroy()

    def on_clear_history(self, action, value):
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Clear All History?",
            body="This will permanently delete all saved chat sessions. Continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("clear", "Clear All")
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        
        dialog.connect("response", self.on_clear_history_response)
        dialog.present()

    def on_clear_history_response(self, dialog, response):
        if response == "clear":
            try:
                for f in os.listdir(self.history_dir):
                    if f.endswith(".json"):
                        os.remove(os.path.join(self.history_dir, f))
                self.sessions_metadata = []
                self.entry.get_buffer().set_text("")
                self.chat_box_remove_all()
                self.history = []
                self.current_session_id = None
                self.update_model_ui()
                self.add_system_message("History cleared.")
                self.update_history_ui()
            except Exception as e:
                self.add_system_message(f"Error clearing history: {e}")
        dialog.destroy()

    def on_history_row_activated(self, listbox, row):
        index = row.get_index()
        if index < len(self.sessions_metadata):
            session_id = self.sessions_metadata[index]["id"]
            
            if self.current_session_id == session_id:
                return
            
            if flm.is_model_in_memory(self.server_process) or self.server_process or self.current_model:
                dialog = Adw.MessageDialog(
                    transient_for=self.win,
                    heading="Switch Chat?",
                    body="Switching chats will unload the current model and clear the current chat session. Continue?"
                )
                dialog.add_response("cancel", "Cancel")
                dialog.add_response("switch", "Switch")
                dialog.set_response_appearance("switch", Adw.ResponseAppearance.DESTRUCTIVE)
                dialog.connect("response", self.on_switch_dialog_response, session_id)
                dialog.present()
            else:
                self.run_task(self.load_session(session_id))

    def on_switch_dialog_response(self, dialog, response, session_id):
        if response == "switch":
            self.cancel_ai_task()
            
            self.execute_eject()
            self.run_task(self.load_session(session_id))
        dialog.destroy()

    def save_session(self):
        sessions.save_session(self)

    async def load_session(self, session_id):
        path = os.path.join(self.history_dir, f"{session_id}.json")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.current_session_id = session_id
                self.history = data.get("messages", [])
                self.current_model = data.get("model")
                
                self.chat_box_remove_all()
                
                for msg in self.history:
                    self.add_message(msg.get("content", ""), msg["role"] == "user", msg.get("image"))
                
                if self.current_model and self.current_model != "none":
                    self.model_btn.set_label(self.current_model)
                    self.add_system_message("Resources clearing... please wait.")
                    await asyncio.sleep(1.5)
                    self.server_process = flm.start_flm_serve(self.current_model, self.server_process)
                    self.run_task(self.wait_for_server())
                
                self.update_model_ui()
        except Exception as e:
            self.add_system_message(f"Error loading session: {e}")

    def on_new_chat(self, btn):
        if not self.history:
            self.execute_new_chat()
            return
            
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Start New Chat?",
            body="Starting a new chat will clear the current conversation. Continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("new", "Start New Chat")
        dialog.set_response_appearance("new", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self.on_new_chat_response)
        dialog.present()

    def on_new_chat_response(self, dialog, response):
        if response == "new":
            self.execute_new_chat()

    def show_welcome_message(self):
        self.chat_box_remove_all()
        # Disable model selection on welcome screen
        self.model_btn.set_sensitive(False)
        self.model_btn.set_tooltip_text("Start a new chat to select a model.")
        
        # Disable interaction
        self.entry.set_sensitive(False)
        self.btn_send.set_sensitive(False)

        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        welcome_box.set_valign(Gtk.Align.CENTER)
        welcome_box.set_halign(Gtk.Align.CENTER)
        
        icon = Gtk.Image(icon_name="document-new-symbolic")
        icon.set_pixel_size(64)
        icon.set_halign(Gtk.Align.CENTER)
        welcome_box.append(icon)
        
        info_text = (
            "Welcome to FastFlowLM-gtk!\n\n"
            "This app is a graphical interface for the FastFlowLM engine.\n\n"
            "• Modern, distraction-free desktop UI\n"
            "• Advanced session & history management\n"
            "• Search history with live message previews\n"
            "• Markdown bolding & visual formatting support\n"
            "• Image attachment support (for vision models)\n"
            "• Customizable theme colors\n\n"
            "Please click 'New Chat' to begin."
        )
        
        label = Gtk.Label(label=info_text)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_halign(Gtk.Align.CENTER)
        welcome_box.append(label)
        
        link = Gtk.LinkButton(uri="https://github.com/FastFlowLM/FastFlowLM", label="Visit FastFlowLM on GitHub")
        link.set_halign(Gtk.Align.CENTER)
        welcome_box.append(link)
        
        # Center the box inside the chat area
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_box.set_valign(Gtk.Align.CENTER)
        outer_box.append(welcome_box)
        
        self.chat_box.append(outer_box)

    def chat_box_remove_all(self):
        return display.chat_box_remove_all(self)

    def execute_new_chat(self):
        self.save_session()
        self.entry.get_buffer().set_text("")
        self.chat_box_remove_all()
        self.history = []
        self.current_session_id = str(int(time.time()))
        # Re-enable model selection
        self.model_btn.set_sensitive(True)
        self.update_model_ui()
        self.add_system_message("New session started.")

    def execute_eject(self):
        self.current_model = None
        self.update_model_ui()

    def on_key_pressed(self, ctrl, keyval, keycode, state):
        return handlers.on_key_pressed(self, ctrl, keyval, keycode, state)

    def on_send(self, widget):
        handlers.on_send(self, widget)

    async def get_ai_response(self):
        try:
            if not self.current_model:
                self.add_system_message("Please select a model first.")
                return

            thinking_label = Gtk.Label(label="Thinking...")
            thinking_label.add_css_class("dim-label")
            self.chat_box.append(thinking_label)
            
            bubble = self.add_message("", is_user=False)
            full_content = ""
            
            messages = []
            for msg in self.history:
                content = [{"type": "text", "text": msg.get("content", "")}]
                if msg.get("image"):
                    try:
                        import base64
                        with open(msg["image"], "rb") as image_file:
                            encoded = base64.b64encode(image_file.read()).decode('utf-8')
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}})
                    except Exception as e:
                        print(f"Error encoding image: {e}")
                messages.append({"role": msg["role"], "content": content})

            stream = await network.get_ai_response(self, bubble, thinking_label, messages)
            if not stream:
                self.add_system_message("Error: Network endpoint request failed.")
                return
                
            data_stream = Gio.DataInputStream.new(stream)
            while True:
                line_bytes, length = await data_stream.read_line_async(GLib.PRIORITY_DEFAULT, None)
                if line_bytes is None: break
                
                line = line_bytes.decode('utf-8').strip()
                if not line or not line.startswith("data: "): continue
                
                content = line[6:]
                if content == "[DONE]": break
                
                try:
                    chunk = json.loads(content)
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        text = chunk['choices'][0].get('delta', {}).get('content')
                        if text:
                            if thinking_label.get_parent() == self.chat_box:
                                self.chat_box.remove(thinking_label)
                            full_content += text
                            def update_bubble():
                                try:
                                    bubble.set_markup(utils.markdown_to_pango(full_content))
                                except Exception as e:
                                    print(f"Markup error: {e}")
                            GLib.idle_add(update_bubble)
                    self.scroll_to_bottom()
                except Exception as e:
                    print(f"Error parsing chunk: {e}")
            
            self.history.append({"role": "assistant", "content": full_content})
            self.save_session()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.add_system_message(f"Connection mapping error: {str(e)}")
        finally:
            self.is_sending = False
            
            # Robust UI unlock upon completion
            def unlock_ui():
                self.input_box.set_sensitive(True)
                self.entry.set_editable(True)
                self.btn_attach.set_sensitive(self.is_current_model_capable())
                self.entry.grab_focus()
            GLib.idle_add(unlock_ui)
            
            if thinking_label.get_parent() == self.chat_box:
                GLib.idle_add(lambda: self.chat_box.remove(thinking_label))

    def on_choose_color(self, action, value):
        dialog = Gtk.ColorDialog.new()
        dialog.choose_rgba(self.win, None, None, self.on_color_picked, None)

    def on_color_picked(self, dialog, result, data):
        try:
            color = dialog.choose_rgba_finish(result)
            hex_color = "#{:02x}{:02x}{:02x}".format(int(color.red * 255), int(color.green * 255), int(color.blue * 255))
            theme.apply_theme(self, hex_color)
            
            config_path = os.path.expanduser("~/.config/flm/theme.json")
            with open(config_path, "w") as f:
                json.dump({"accent_color": hex_color}, f)
        except Exception as e:
            logging.error(f"Error applying color: {e}")

    def do_shutdown(self):
        self.save_session()
        if self.server_process:
            self.server_process.terminate()
        Adw.Application.do_shutdown(self)
