"""
Module for model management and installation.
Handles server lifecycle, model downloads, and UI synchronization.
"""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib
import asyncio
import subprocess
import flm
import re
from typing import Optional

async def init_server(app) -> None:
    """Initializes available models and updates UI."""
    app.models = flm.get_all_models()
    update_model_ui(app)

async def wait_for_server(app) -> None:
    """Polls server process until it is active or times out."""
    for _ in range(25):
        await asyncio.sleep(1)
        if flm.is_model_in_memory(app.server_process):
            app.add_system_message("Model active in host process space.")
            GLib.timeout_add_seconds(2, app.clear_status_labels)
            return
    app.add_system_message("Error: Runtime server failed to build on subsystem architecture.")

def confirm_download(app, model_data: dict) -> None:
    """Shows confirmation dialog before starting model download."""
    model_name = model_data['model']
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Download Model?",
        body=f"Do you want to download {model_name}?"
    )
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("download", "Download")
    dialog.set_response_appearance("download", Adw.ResponseAppearance.SUGGESTED)
    
    dialog.connect("response", lambda d, r: on_download_response(app, d, r, model_name))
    dialog.present()

def on_download_response(app, dialog: Adw.MessageDialog, response: str, model_name: str) -> None:
    """Callback for download confirmation."""
    if response == "download":
        app.add_system_message(f"Starting download: {model_name}")
        app.run_task(download_model(app, model_name))
    dialog.destroy()

async def download_model(app, model_name: str) -> None:
    """Executes model download with real-time progress parsing."""
    app.downloading_models.add(model_name)
    
    progress = Gtk.ProgressBar()
    progress.set_fraction(0.0)
    progress.set_show_text(True)
    progress.set_margin_top(10)
    progress.set_margin_bottom(10)
    progress.add_css_class("suggested-action")
    
    app.chat_box.append(progress)
    update_model_ui(app)
    
    try:
        process = await asyncio.create_subprocess_exec(
            "flm", "pull", model_name,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        downloading_started = False
        
        while True:
            chunk = await process.stdout.read(1024)
            if not chunk:
                break
            
            output = chunk.decode('utf-8', errors='ignore')
            lines = output.split('\r')
            
            for line in lines:
                match = re.search(r"Downloading:\s+(\d+(\.\d+)?)%", line)
                if match:
                    downloading_started = True
                    percent = float(match.group(1)) / 100.0
                    GLib.idle_add(progress.set_fraction, percent)
                    GLib.idle_add(progress.set_text, f"Downloading {model_name}: {match.group(1)}%")
                elif "Download completed" in line and downloading_started:
                    GLib.idle_add(progress.set_text, "Download completed")
                    GLib.idle_add(progress.set_fraction, 1.0)
        
        await process.wait()
        if process.returncode == 0:
            app.add_system_message(f"Successfully downloaded {model_name}")
        else:
            app.add_system_message(f"Failed to download {model_name}")
    except Exception as e:
        app.add_system_message(f"Download error: {str(e)}")
    finally:
        app.chat_box.remove(progress)
        app.downloading_models.discard(model_name)
        app.models = flm.get_all_models()
        update_model_ui(app)

def update_model_ui(app) -> None:
    """Refreshes the model selector button UI state."""
    if not app.models:
        app.models = flm.get_all_models()
    
    if app.current_model:
        label_text = app.current_model
        model_data = next((m for m in app.models if m['model'] == app.current_model), None)
        if model_data and model_data.get('vlm', False):
            label_text = "👁 " + label_text
        app.model_btn.set_label(label_text)
    else:
        app.model_btn.set_label("Select a model to start")
    
    any_installed = any(m.get('installed', False) for m in app.models)
    if not any_installed:
        app.btn_new.set_sensitive(False)
        app.btn_new.set_tooltip_text("Install a model to start a new chat.")
    else:
        app.btn_new.set_sensitive(True)
        app.btn_new.set_tooltip_text("New Chat")

    is_running = flm.is_model_in_memory(app.server_process)
    ram_ok = flm.has_sufficient_ram()
    
    app.btn_attach.set_sensitive(app.is_current_model_capable())
    
    app.entry.set_sensitive(app.current_session_id is not None)
    app.btn_send.set_sensitive(app.current_session_id is not None)
    
    if app.current_session_id is None:
        app.model_btn.set_sensitive(False)
        app.model_btn.set_tooltip_text("Start a new chat to select a model.")
    elif not app.allow_mid_chat_switch and app.history:
        app.model_btn.set_sensitive(False)
        app.model_btn.set_tooltip_text("Model locked in memory during active conversation.")
    elif not ram_ok and not is_running:
        app.model_btn.set_sensitive(False)
        app.model_btn.set_tooltip_text("System RAM is critically low. Free memory to load models.")
    else:
        app.model_btn.set_sensitive(True)
        app.model_btn.set_tooltip_text("Select Model")

    popover = Gtk.Popover()
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_min_content_height(350)
    scrolled.set_min_content_width(300)
    
    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    
    for m in app.models:
        model_name = m['model']
        is_installed = m.get('installed', False)
        is_downloading = model_name in app.downloading_models
        
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)

        label_text = f"⬇ Downloading {model_name}..." if is_downloading else model_name
        if m.get('vlm', False):
            label_text = "👁 " + label_text
        label = Gtk.Label(label=label_text)
        label.set_xalign(0)
            
        if is_downloading:
            row.set_sensitive(False)
        elif not is_installed:
            label.add_css_class("uninstalled-model-label")
        else:
            label.add_css_class("installed-model-label")
            del_btn = Gtk.Button(icon_name="user-trash-symbolic")
            del_btn.add_css_class("delete-btn")
            del_btn.set_has_frame(False)
            del_btn.set_tooltip_text("Delete Model")
            # Connect the button click only once
            del_btn.connect("clicked", lambda b, m=model_name: confirm_delete(app, m, popover))
            box.append(del_btn)
            
        box.append(label)
        row.set_child(box)
        listbox.append(row)
        
    listbox.connect("row-activated", lambda lb, row: on_row_activated(app, lb, row, popover))
    
    scrolled.set_child(listbox)
    popover.set_child(scrolled)
    app.model_btn.set_popover(popover)

def confirm_delete(app, model_name: str, popover: Gtk.Popover) -> None:
    """Shows confirmation dialog before deleting a model, closing popover first."""
    popover.popdown()
    
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Delete Model?",
        body=f"Are you sure you want to permanently delete {model_name}?"
    )
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("delete", "Delete")
    dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
    
    def on_response(dialog, response):
        on_delete_response(app, dialog, response, model_name)

    dialog.connect("response", on_response)
    dialog.present()

def on_delete_response(app, dialog: Adw.MessageDialog, response: str, model_name: str) -> None:
    """Callback for deletion confirmation."""
    if response == "delete":
        app.add_system_message(f"Removing {model_name}...")
        try:
            subprocess.run(["flm", "remove", model_name], check=True)
            app.add_system_message(f"Removed {model_name}")
            app.models = flm.get_all_models()
            update_model_ui(app)
        except Exception as e:
            app.add_system_message(f"Deletion error: {str(e)}")
    dialog.destroy()

def on_row_activated(app, listbox: Gtk.ListBox, row: Gtk.ListBoxRow, popover: Gtk.Popover) -> None:
    """Activated when a model row is selected."""
    index = row.get_index()
    if index < len(app.models):
        on_model_selected(app, None, app.models[index], popover)

def on_model_selected(app, btn: Optional[Gtk.Button], model_data: dict, popover: Gtk.Popover) -> None:
    """Handles model selection and server initialization."""
    model_name = model_data['model']
    is_installed = model_data.get('installed', False)
    popover.popdown()

    if not is_installed:
        confirm_download(app, model_data)
        return

    app.current_model = model_name
    app.model_btn.set_label(model_name)
    
    if app.history:
        app.save_session()
    
    app.add_system_message(f"Starting process matrix for {model_name}...")
    app.server_process = flm.start_flm_serve(model_name, app.server_process)
    app.run_task(wait_for_server(app))
