import init_gi
from gi.repository import Gtk, Gdk, GLib, Adw
import display
import os
import flm
import time
from typing import Optional

def on_key_pressed(app, ctrl: Gtk.EventControllerKey, keyval: int, keycode: int, state: Gdk.ModifierType) -> bool:
    # handle enter and shift+enter
    if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
        if state & Gdk.ModifierType.SHIFT_MASK:
            # insert newline
            buffer = app.entry.get_buffer()
            buffer.insert_at_cursor("\n")
            return True
        else:
            on_send(app, None)
            return True
    return False

def on_send(app, widget: Optional[Gtk.Widget]) -> None:
    # send prompt to model
    import logging
    if app.is_sending:
        return
        
    buffer = app.entry.get_buffer()
    start, end = buffer.get_bounds()
    text = buffer.get_text(start, end, True).strip()
    
    if not text and not app.selected_attachments:
        return
    
    # generate unique session ID if missing
    if not app.current_session_id:
        app.current_session_id = str(int(time.time()))
        
    app.is_sending = True
    
    # lock UI during generation
    app.input_box.set_sensitive(False)
    app.set_entry_locked(True)
    if hasattr(app, "update_shortcuts_sensitivity"):
        app.update_shortcuts_sensitivity()
        
    # Launch async task to read files off the main thread
    app.run_task(app._on_send_async(text, app.selected_attachments.copy()))
    app.selected_attachments = []
    app.update_thumbnail()

def on_attach_clicked(app, btn):
    if len(app.selected_attachments) >= 3:
        dialog = Adw.MessageDialog(
            transient_for=app.win,
            heading="Attachment Limit Reached",
            body="You can only select up to 3 attachments at once."
        )
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
        return

    app.btn_attach.set_sensitive(False)
    dialog = Gtk.FileChooserNative.new("Select Files", app.win, Gtk.FileChooserAction.OPEN, "Open", "Cancel")
    dialog.set_select_multiple(True)
    
    # configure file filters
    filter = Gtk.FileFilter()
    filter.set_name("All Supported Files")
    
    # allow images if VLM capable
    if app.is_current_model_vlm():
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/webp")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.jpeg")
        filter.add_pattern("*.webp")
        
    # allow text/code formats
    filter.add_mime_type("text/plain")
    filter.add_pattern("*.txt")
    filter.add_pattern("*.py")
    filter.add_pattern("*.cpp")
    filter.add_pattern("*.c")
    filter.add_pattern("*.h")
    filter.add_pattern("*.sh")
    filter.add_pattern("*.js")
    filter.add_pattern("*.ts")
    filter.add_pattern("*.css")
    filter.add_pattern("*.json")
    filter.add_pattern("*.md")
    filter.add_pattern("*.html")
    
    dialog.add_filter(filter)
    dialog.connect("response", lambda d, r: on_file_selected(app, d, r))
    dialog.show()

def on_file_selected(app, dialog, response):
    app.btn_attach.set_sensitive(app.is_current_model_capable())
    if response == Gtk.ResponseType.ACCEPT:
        files_model = dialog.get_files()
        num_files = files_model.get_n_items()
        added_any_exceeded = False
        
        for i in range(num_files):
            if len(app.selected_attachments) >= 3:
                added_any_exceeded = True
                break
                
            file = files_model.get_item(i)
            path = file.get_path()
            if path:
                is_img = path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
                if is_img and not app.is_current_model_vlm():
                    warn_dialog = Adw.MessageDialog(
                        transient_for=app.win,
                        heading="Vision Model Required",
                        body="The current model does not support images. Please switch to a vision model (VLM) or attach a text/code file instead."
                    )
                    warn_dialog.add_response("ok", "OK")
                    warn_dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
                    warn_dialog.present()
                else:
                    name = os.path.basename(path)
                    att_type = "image" if is_img else "text"
                    if not any(att["path"] == path for att in app.selected_attachments):
                        app.selected_attachments.append({"path": path, "name": name, "type": att_type})
        
        app.update_thumbnail()
        
        if added_any_exceeded:
            limit_dialog = Adw.MessageDialog(
                transient_for=app.win,
                heading="Attachment Limit Reached",
                body="You can only select up to 3 attachments at once. Some files were not added."
            )
            limit_dialog.add_response("ok", "OK")
            limit_dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
            limit_dialog.present()
            
    dialog.destroy()

def on_allow_switch_toggled(app, action, value):
    new_state = not action.get_state().get_boolean()
    
    if new_state:
        dialog = Adw.MessageDialog(
            transient_for=app.win,
            heading="Enable Model Switching?",
            body="Enabling model switching allows you to change the active model at any time, which may reload the model server. Continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("enable", "Enable")
        dialog.set_response_appearance("enable", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda d, r: complete_switch_toggle(app, action, r))
        dialog.present()
    else:
        complete_switch_toggle(app, action, "enable")

def complete_switch_toggle(app, action, response):
    if response == "enable":
        new_state = not action.get_state().get_boolean()
        action.set_state(GLib.Variant.new_boolean(new_state))
        app.allow_mid_chat_switch = new_state
        app.update_model_ui()

def on_history_row_activated(app, listbox, row):
    # Unselect the dashboard visually right away to prevent dual highlight
    if hasattr(app, 'nav_list') and app.nav_list:
        app.nav_list.unselect_all()
        
    session_id = getattr(row, 'session_id', None)
    if not session_id: return
    
    if app.current_session_id == session_id:
        return

    if flm.is_model_in_memory(app.server_process) or app.server_process or (app.current_model and app.current_model != "none"):
        dialog = Adw.MessageDialog(
            transient_for=app.win,
            heading="Switch Chat?",
            body="Switching chats will unload the current model and clear the current chat session. Continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("switch", "Switch")
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda d, r: on_switch_dialog_response(app, d, r, session_id))
        dialog.present()
    else:
        app.run_task(app.load_session(session_id))

def on_switch_dialog_response(app, dialog, response, session_id):
    if response == "switch":
        if hasattr(app, 'nav_list'):
            app.nav_list.unselect_all()
        display.cancel_ai_task(app)
        app.execute_eject()
        app.run_task(app.load_session(session_id))
    else:
        # User cancelled! Restore selection highlight.
        if getattr(app, 'is_welcome_screen', False):
            if hasattr(app, 'nav_list') and app.nav_list:
                app.nav_list.select_row(app.nav_list.get_row_at_index(0))
            app.history_list.unselect_all()
        elif app.current_session_id:
            for row in app.history_list:
                if getattr(row, 'session_id', None) == app.current_session_id:
                    app.history_list.select_row(row)
                    break
        else:
            app.history_list.unselect_all()
    dialog.destroy()

def on_delete_clicked(app, btn, session_id):
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Delete Chat?",
        body="Are you sure you want to permanently delete this conversation?"
    )
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("delete", "Delete")
    dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        
    dialog.connect("response", lambda d, r: on_delete_response(app, d, r, session_id))
    dialog.present()

def on_delete_response(app, dialog, response, session_id):
    if response == "delete":
        path = os.path.join(app.history_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
        
        app.sessions_metadata = [m for m in app.sessions_metadata if m["id"] != session_id]
        
        fav = getattr(app, "favourited_chat", None)
        if fav is not None and str(fav) == str(session_id):
            app.favourited_chat = None
            app.save_config()
            
        if app.current_session_id == session_id:
            app.current_session_id = None
            app.history = []
            app.update_model_ui()
            app.show_welcome_message()
            display.add_system_message(app, "Session deleted.")
        
        app.update_history_ui()
    dialog.destroy()

def on_clear_history(app, action, value):
    dialog = Adw.MessageDialog(
        transient_for=app.win,
        heading="Clear All History?",
        body="This will permanently delete all saved chat sessions. Continue?"
    )
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("clear", "Clear All")
    dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
    
    dialog.connect("response", lambda d, r: on_clear_history_response(app, d, r))
    dialog.present()

def on_clear_history_response(app, dialog, response):
    if response == "clear":
        try:
            for f in os.listdir(app.history_dir):
                if f.endswith(".json"):
                    os.remove(os.path.join(app.history_dir, f))
            app.sessions_metadata = []
            app.current_session_id = None
            app.favourited_chat = None
            app.save_config()
            app.history = []
            if hasattr(app, '_search_cache'):
                app._search_cache = {}
            app.update_model_ui()
            app.show_welcome_message()
            display.add_system_message(app, "History cleared.")
            app.update_history_ui()
        except Exception as e:
            display.add_system_message(app, f"Error clearing history: {e}")
    dialog.destroy()


def on_files_dropped(app, file_list):
    if not file_list:
        return False

    # Respect the same 3-attachment hard limit as the button path
    if len(getattr(app, "selected_attachments", [])) >= 3:
        dialog = Adw.MessageDialog(
            transient_for=app.win,
            heading="Attachment Limit Reached",
            body="You can only have up to 3 attachments at once."
        )
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
        return False

    # Try to extract paths from Gdk.FileList (modern GTK4 way)
    paths = []
    try:
        if hasattr(file_list, "get_files"):
            gfiles = file_list.get_files()
            for i in range(gfiles.get_n_items()):
                f = gfiles.get_item(i)
                p = f.get_path() if hasattr(f, "get_path") else None
                if p:
                    paths.append(p)
        else:
            # Fallback for some drag payloads
            for f in file_list:
                if hasattr(f, "get_path"):
                    p = f.get_path()
                    if p:
                        paths.append(p)
    except Exception as e:
        import logging
        logging.error(f"file list error: {e}")
        return False

    if not paths:
        return False

    added_any = False
    added_any_exceeded = False

    for path in paths:
        if len(app.selected_attachments) >= 3:
            added_any_exceeded = True
            break

        if not path or not os.path.exists(path):
            continue

        lower = path.lower()
        is_img = lower.endswith(('.png', '.jpg', '.jpeg', '.webp'))

        if is_img and not app.is_current_model_vlm():
            warn = Adw.MessageDialog(
                transient_for=app.win,
                heading="Vision Model Required",
                body="The current model does not support images. Please switch to a vision model (VLM) or drop a text/code file instead."
            )
            warn.add_response("ok", "OK")
            warn.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
            warn.present()
            continue

        name = os.path.basename(path)
        att_type = "image" if is_img else "text"

        if not any(att["path"] == path for att in app.selected_attachments):
            app.selected_attachments.append({"path": path, "name": name, "type": att_type})
            added_any = True

    if added_any:
        app.update_thumbnail()

    if added_any_exceeded:
        limit_dialog = Adw.MessageDialog(
            transient_for=app.win,
            heading="Attachment Limit Reached",
            body="You can only select up to 3 attachments at once. Some files were not added."
        )
        limit_dialog.add_response("ok", "OK")
        limit_dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        limit_dialog.present()

    return True
