# models
from gi.repository import Gtk, Adw, GLib
import asyncio
import subprocess
import os
import flm
import re
import display
import utils
from typing import Optional

async def init_server(app) -> None:
    # get models
    app.models = flm.get_all_models()
    app.update_model_ui()

async def wait_for_server(app) -> None:
    # wait for server
    app.model_loading = True
    app.set_entry_locked(True)
    app.btn_send.set_sensitive(False)
    app.update_model_ui()
    
    target_model = app.current_model
    target_process = app.server_process
    
    for i in range(45):
        if app.current_model != target_model or app.server_process != target_process:
            app.model_loading = False
            return
            
        # check if server died
        if target_process and target_process.poll() is not None:
            rc = target_process.poll()
            if rc not in (15, -15, 9, -9) and not (rc == 1 and target_model != app.current_model):
                display.clear_status_labels(app)
                display.add_system_message(app, f"Error: Server process exited with code {rc}.")
                display.add_system_message(app, "Check ~/.config/flm/server.log for details.")
            app.model_loading = False
            app.update_model_ui()
            return

        if flm.is_server_ready(target_model, server_process=target_process):
            display.add_system_message(app, f"{target_model} is ready.")
            GLib.timeout_add_seconds(2, lambda: display.clear_status_labels(app))
            app.model_loading = False
            app.update_model_ui()
            return
            
        if i % 5 == 0:
            if target_model and target_model != "none":
                display.add_system_message(app, f"Waiting for {target_model} to initialize...")
        
        await asyncio.sleep(1)
            
    display.clear_status_labels(app)
    if target_model and target_model != "none":
        display.add_system_message(app, "Server startup timed out. Please try loading the model again.")
    app.model_loading = False
    app.update_model_ui()


def confirm_download(app, model_data: dict) -> None:
    # prompt user before downloading
    if len(app.downloading_models) > 0:
        display.add_system_message(app, "A download is already in progress. Please wait.")
        return

    model_name = model_data['model']
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Download Model?",
        body=f"Are you sure you want to download {model_name}? \n\nNote: The chat interface, sidebar, and other controls will be locked while the download is in progress."
    )
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("download", "Download and Lock Interface")
    dialog.set_response_appearance("download", Adw.ResponseAppearance.SUGGESTED)
    
    dialog.connect("response", lambda d, r: on_download_response(app, d, r, model_name))
    dialog.present()

def on_download_response(app, dialog: Adw.MessageDialog, response: str, model_name: str) -> None:
    if response == "download":
        display.add_system_message(app, f"Starting download: {model_name}")
        app.run_task(download_model(app, model_name))
    dialog.destroy()

async def download_model(app, model_name: str) -> None:
    # download model files
    app.downloading_models.add(model_name)
    
    progress = Gtk.ProgressBar()
    progress.set_fraction(0.0)
    progress.set_show_text(True)
    progress.set_margin_top(10)
    progress.set_margin_bottom(10)
    progress.add_css_class("suggested-action")
    
    app.chat_box.append(progress)
    app.update_model_ui()
    
    try:
        process = await asyncio.create_subprocess_exec(
            "stdbuf", "-oL", "-eL", "flm", "pull", model_name, "--force",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        downloading_started = False
        
        while True:
            chunk = await process.stdout.read(1024)
            if not chunk:
                break
            
            output = chunk.decode('utf-8', errors='ignore')
            lines = output.splitlines()
            
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
            display.add_system_message(app, f"Successfully downloaded {model_name}")
            display.add_system_message(app, f"Starting {model_name}...")
            app.server_process = flm.start_flm_serve(model_name, app.server_process, pmode=app.power_mode, ctx_len=app.context_len)
            app.run_task(wait_for_server(app))
        else:
            display.add_system_message(app, f"Failed to download {model_name}")
    except Exception as e:
        display.add_system_message(app, f"Download error: {str(e)}")
    finally:
        app.downloading_models.discard(model_name)
        app.models = flm.get_all_models()
        
        def finish_download_ui():
            if progress.get_parent() == app.chat_box:
                app.chat_box.remove(progress)
            app.update_model_ui()
        GLib.idle_add(finish_download_ui)

def update_model_ui(app) -> None:
    # sync model UI states
    app.models = flm.get_all_models()
    
    is_downloading_any = len(app.downloading_models) > 0
    download_msg = "Please wait for the current download to complete."
    
    # lock UI during download
    app.btn_new.set_sensitive(not is_downloading_any)
    app.history_list.set_sensitive(not is_downloading_any)
    if hasattr(app, 'nav_list') and app.nav_list:
        app.nav_list.set_sensitive(not is_downloading_any)
    if is_downloading_any:
        app.btn_new.set_tooltip_text(download_msg)
        app.history_list.set_tooltip_text(download_msg)
        if hasattr(app, 'nav_list') and app.nav_list:
            app.nav_list.set_tooltip_text(download_msg)
        app.sidebar_box.set_tooltip_text(download_msg)
    else:
        app.btn_new.set_tooltip_text("New Chat")
        app.history_list.set_tooltip_text(None)
        if hasattr(app, 'nav_list') and app.nav_list:
            app.nav_list.set_tooltip_text(None)
        app.sidebar_box.set_tooltip_text(None)
    
    if app.current_model and app.current_model != "none":
        label_text = app.current_model
        model_data = next((m for m in app.models if m['model'] == app.current_model), None)
        if model_data and model_data.get('vlm', False):
            label_text = "👁 " + label_text
        app.model_btn.set_label(label_text)
    else:
        app.model_btn.set_label("Select a model to start")
    
    # evaluate model switching eligibility
    app.model_btn.set_sensitive(not is_downloading_any and not getattr(app, 'is_welcome_screen', False))
    if is_downloading_any:
        app.model_btn.set_tooltip_text(download_msg)
    elif getattr(app, 'is_welcome_screen', False):
        app.model_btn.set_tooltip_text("Start a new chat to select a model.")
    else:
        app.model_btn.set_tooltip_text("Select Model")

    is_running = flm.is_server_ready(app.current_model, server_process=getattr(app, 'server_process', None)) if app.current_model else False
    ram_ok = flm.has_sufficient_ram()
    
    has_model = app.current_model is not None and app.current_model != "none"
    
    # check if downloaded
    is_current_installed = False
    if has_model:
        m_data = next((m for m in app.models if m['model'] == app.current_model), None)
        is_current_installed = m_data is not None and m_data.get('installed', False)

    # determine message sending capability
    is_input_allowed = (has_model and 
                        is_current_installed and 
                        not is_downloading_any and
                        is_running)
    
    app.set_entry_locked(not is_input_allowed)
    app.btn_send.set_sensitive(is_input_allowed)
    app.btn_attach.set_sensitive(app.is_current_model_capable() and is_current_installed and not is_downloading_any and is_running)
    
    if is_downloading_any:
        app.entry.set_tooltip_text(download_msg)
        app.btn_send.set_tooltip_text(download_msg)
    elif has_model and is_current_installed and not is_running:
        app.entry.set_tooltip_text("Model is unloaded. Click the Load button in the header bar to load it.")
        app.btn_send.set_tooltip_text("Load model to send messages")
    else:
        app.entry.set_tooltip_text("Type your message here")
        app.btn_send.set_tooltip_text("Send message")
    
    if not app.allow_mid_chat_switch and app.history:
        app.model_btn.set_sensitive(False)
        app.model_btn.set_tooltip_text("Model locked in memory during active conversation.")
    elif not ram_ok and not is_running:
        app.model_btn.set_sensitive(False)
        app.model_btn.set_tooltip_text("System RAM is critically low. Free memory to load models.")

    popover = Gtk.Popover()
    
    # construct model dropdown layout
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    
    # section header
    header_label = Gtk.Label(label="AVAILABLE MODELS")
    header_label.add_css_class("model-picker-header")
    header_label.set_xalign(0.0)
    main_box.append(header_label)
    
    # separator
    separator = Gtk.Separator()
    main_box.append(separator)
    
    # scroll container
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_min_content_height(350)
    scrolled.set_min_content_width(320)
    main_box.append(scrolled)
    
    listbox = Gtk.ListBox()
    listbox.add_css_class("model-picker-list")
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    
    for m in app.models:
        model_name = m['model']
        is_installed = m.get('installed', False)
        is_downloading = model_name in app.downloading_models
        is_vlm = m.get('vlm', False)
        is_active = (app.current_model == model_name)
        
        row = Gtk.ListBoxRow()
        row.add_css_class("model-picker-row")
        if is_active:
            row.add_css_class("selected-model-row")
            
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        # set icon based on model type
        logo_file = utils.get_model_logo_file(model_name)
        logo_loaded = False
        
        if logo_file:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_dir, "assets", logo_file)
            if os.path.exists(logo_path):
                icon = Gtk.Image.new_from_file(logo_path)
                icon.set_pixel_size(24)
                icon.add_css_class("model-logo-img")
                box.append(icon)
                logo_loaded = True
                
        if not logo_loaded:
            icon_name = "view-reveal-symbolic" if is_vlm else "cpu-symbolic"
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.add_css_class("model-icon")
            box.append(icon)
        
        # layout name and status badges
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_hexpand(True)
        
        name_label = Gtk.Label(label=model_name)
        name_label.add_css_class("model-name-label")
        name_label.set_xalign(0.0)
        content_box.append(name_label)
        
        # build status badges
        badges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        if is_active:
            active_badge = Gtk.Label(label="Active")
            active_badge.add_css_class("model-badge")
            active_badge.add_css_class("badge-active")
            badges_box.append(active_badge)
            
        if is_installed:
            inst_badge = Gtk.Label(label="Installed")
            inst_badge.add_css_class("model-badge")
            inst_badge.add_css_class("badge-installed")
            badges_box.append(inst_badge)
        elif is_downloading:
            dl_badge = Gtk.Label(label="Downloading...")
            dl_badge.add_css_class("model-badge")
            dl_badge.add_css_class("badge-downloading")
            badges_box.append(dl_badge)
        else:
            avail_badge = Gtk.Label(label="Available")
            avail_badge.add_css_class("model-badge")
            avail_badge.add_css_class("badge-available")
            badges_box.append(avail_badge)
            
        if is_vlm:
            vlm_badge = Gtk.Label(label="👁 Vision")
            vlm_badge.add_css_class("model-badge")
            vlm_badge.add_css_class("badge-vlm")
            badges_box.append(vlm_badge)
            
        content_box.append(badges_box)
        box.append(content_box)
        
        # action buttons
        right_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right_area.set_valign(Gtk.Align.CENTER)
        
        if is_downloading:
            # loading spinner during download
            spinner = Gtk.Spinner()
            spinner.start()
            right_area.append(spinner)
            row.set_sensitive(False)
            name_label.add_css_class("dim-label")
        elif is_active:
            # checkmark for active model
            check_icon = Gtk.Image.new_from_icon_name("object-select-symbolic")
            check_icon.add_css_class("model-check-icon")
            right_area.append(check_icon)
        else:
            if is_installed:
                # details button
                info_btn = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
                info_btn.add_css_class("flat")
                info_btn.add_css_class("info-btn")
                info_btn.set_tooltip_text("Model Details")
                info_btn.connect("clicked", lambda b, m=m: show_model_info(app, m))
                right_area.append(info_btn)
                
                # trash button
                del_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic")
                del_btn.add_css_class("flat")
                del_btn.add_css_class("delete-btn")
                del_btn.set_tooltip_text("Delete Model")
                del_btn.connect("clicked", lambda b, m_data=m: confirm_delete(app, m_data, popover))
                right_area.append(del_btn)
            else:
                # download button
                dl_btn = Gtk.Button.new_from_icon_name("emblem-downloads-symbolic")
                dl_btn.add_css_class("flat")
                dl_btn.add_css_class("download-btn")
                dl_btn.set_tooltip_text("Download Model")
                dl_btn.connect("clicked", lambda b, m_data=m: confirm_download_from_btn(app, m_data, popover))
                right_area.append(dl_btn)
                name_label.add_css_class("uninstalled-model-label")
                
        box.append(right_area)
        row.set_child(box)
        listbox.append(row)
        
    listbox.connect("row-activated", lambda lb, row: on_row_activated(app, lb, row, popover))
    
    scrolled.set_child(listbox)
    popover.set_child(main_box)
    app.model_btn.set_popover(popover)
    
    if hasattr(app, "update_shortcuts_sensitivity"):
        app.update_shortcuts_sensitivity()
        
    if hasattr(app, "update_settings_ui"):
        app.update_settings_ui()

def confirm_download_from_btn(app, model_data: dict, popover: Gtk.Popover) -> None:
    # download click handler
    popover.popdown()
    confirm_download(app, model_data)

def show_model_info(app, model_data: dict) -> None:
    # show model details dialog
    details = (
        f"Model: {model_data.get('model', 'Unknown')}\n"
        f"Installed: {'Yes' if model_data.get('installed') else 'No'}\n"
        f"Vision Support: {'Yes' if model_data.get('vlm') else 'No'}"
    )
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Model Information",
        body=details
    )
    dialog.add_response("ok", "OK")
    dialog.present()

def confirm_delete(app, model_data: dict, popover: Gtk.Popover) -> None:
    # prompt user before deletion
    popover.popdown()
    model_name = model_data['model']
    
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Delete Model?",
        body=f"Are you sure you want to permanently delete {model_name}?"
    )
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("delete", "Delete")
    dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
    
    def on_response(dialog, response):
        on_delete_response(app, dialog, response, model_data)

    dialog.connect("response", on_response)
    dialog.present()

async def delete_model_background(app, model_data: dict) -> None:
    model_name = model_data['model']
    if app.current_model == model_name:
        app.execute_eject()

    display.add_system_message(app, f"Removing {model_name}...")
    
    def perform_deletion():
        # remove model via flm cli
        subprocess.run(["flm", "remove", model_name], check=True)
        
        # purge weights directory
        repo_folder = None
        url = model_data.get('url') or model_data.get('file_url')
        if url:
            parts = url.split('/')
            # guess folder from hf url
            if "huggingface.co" in url and len(parts) >= 5:
                repo_folder = parts[4]
        
        if repo_folder:
            models_dir = os.path.expanduser("~/.config/flm/models")
            target_path = os.path.join(models_dir, repo_folder)
            if os.path.exists(target_path):
                import shutil
                shutil.rmtree(target_path)
                return f"Purged model directory: {repo_folder}"
        return None

    try:
        purge_msg = await asyncio.to_thread(perform_deletion)
        if purge_msg:
            display.add_system_message(app, purge_msg)
        display.add_system_message(app, f"Removed {model_name}")
    except subprocess.CalledProcessError:
        display.add_system_message(app, "Model files were missing. Cleaning up UI.")
    except Exception as e:
        display.add_system_message(app, f"Deletion error: {str(e)}")
    
    # reload models and sync UI
    app.models = flm.get_all_models()
    app.update_model_ui()

def on_delete_response(app, dialog: Adw.MessageDialog, response: str, model_data: dict) -> None:
    # delete response handler
    if response == "delete":
        app.run_task(delete_model_background(app, model_data))
    dialog.destroy()

def on_row_activated(app, listbox: Gtk.ListBox, row: Gtk.ListBoxRow, popover: Gtk.Popover) -> None:
    # list row activated handler
    index = row.get_index()
    if index < len(app.models):
        on_model_selected(app, None, app.models[index], popover)

def on_model_selected(app, btn: Optional[Gtk.Button], model_data: dict, popover: Gtk.Popover) -> None:
    # load active model
    model_name = model_data['model']
    is_installed = model_data.get('installed', False)
    popover.popdown()

    app.current_model = model_name
    if app.history:
        app.save_session()

    if not is_installed:
        display.add_system_message(app, f"Error: Please download {model_name} before starting.")
        confirm_download(app, model_data)
    else:
        display.add_system_message(app, f"Starting process matrix for {model_name}...")
        app.server_process = flm.start_flm_serve(model_name, app.server_process, pmode=app.power_mode, ctx_len=app.context_len)
        app.run_task(wait_for_server(app))

    app.update_model_ui()
