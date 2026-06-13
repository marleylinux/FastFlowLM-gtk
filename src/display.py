# display
from gi.repository import Gtk, Gdk, GLib, GtkSource, Pango
import utils
import logging
from typing import Optional

def create_code_block(code: str, language_id: str) -> Gtk.Widget:
    # code block
    lang_manager = GtkSource.LanguageManager.get_default()
    
    # map markdown language names to GTK source IDs
    lang_map = {
        "python": "python",
        "py": "python",
        "python3": "python",
        "bash": "sh",
        "sh": "sh",
        "shell": "sh",
        "js": "js",
        "javascript": "js",
        "html": "html",
        "css": "css",
        "cpp": "cpp",
        "c++": "cpp",
        "c": "c",
        "json": "json"
    }
    
    target_lang = lang_map.get(language_id.lower(), language_id)
    lang = lang_manager.get_language(target_lang)
    
    buffer = GtkSource.Buffer.new_with_language(lang) if lang else GtkSource.Buffer.new()
    buffer.set_text(code)
    
    # load dark style scheme
    scheme_manager = GtkSource.StyleSchemeManager.get_default()
    scheme = scheme_manager.get_scheme("Adwaita-dark") or scheme_manager.get_scheme("oblivion")
    if scheme:
        buffer.set_style_scheme(scheme)
    
    view = GtkSource.View.new_with_buffer(buffer)
    view.set_editable(False)
    view.set_show_line_numbers(True)
    view.set_monospace(True)
    view.set_wrap_mode(Gtk.WrapMode.WORD)
    view.add_css_class("code-block")
    
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_hexpand(True)
    scrolled.set_vexpand(False)
    scrolled.set_propagate_natural_height(True)
    scrolled.set_min_content_height(100)
    scrolled.set_min_content_width(650)  # comfortable reading width
    scrolled.set_max_content_height(600)
    scrolled.set_child(view)
    
    overlay = Gtk.Overlay()
    overlay.set_child(scrolled)
    
    copy_btn = Gtk.Button.new_from_icon_name("edit-copy-symbolic")
    copy_btn.add_css_class("flat")
    copy_btn.add_css_class("bubble-action-btn")
    copy_btn.set_tooltip_text("Copy Code")
    copy_btn.set_halign(Gtk.Align.END)
    copy_btn.set_valign(Gtk.Align.START)
    copy_btn.set_margin_end(6)
    copy_btn.set_margin_top(6)
    copy_btn.connect("clicked", lambda b: copy_to_clipboard(code))
    
    overlay.add_overlay(copy_btn)
    return overlay

def render_message_chunks(app, bubble_box, text: str) -> Optional[Gtk.Label]:
    if text:
        text = text.strip()
        
    chunks = utils.parse_message(text)
    
    last_bubble = None
    for ctype, content, lang in chunks:
        if ctype == "code":
            bubble_box.append(create_code_block(content, lang))
        else:
            bubble = Gtk.Label()
            bubble.set_wrap(True)
            bubble.set_selectable(True)
            bubble.set_xalign(0)
            bubble.set_use_markup(True)
            try:
                bubble.set_markup(utils.markdown_to_pango(content))
            except Exception as e:
                logging.error(f"Failed to set pango markup: {e}")
                bubble.set_use_markup(False)
                bubble.set_text(content)
            bubble_box.append(bubble)
            last_bubble = bubble
    return last_bubble

def add_message(app, text: str, is_user: bool, attachments = None) -> Gtk.Label:
    # build message bubble layout
    bubble_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    bubble_box.add_css_class("user-bubble" if is_user else "assistant-bubble")
    if is_user:
        bubble_box.set_halign(Gtk.Align.END)
    else:
        bubble_box.set_halign(Gtk.Align.START)
    
    # message header showing sender
    header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    header.add_css_class("bubble-header")
    
    if is_user:
        sender_label = Gtk.Label(label="You")
        sender_label.add_css_class("bubble-user-label")
    else:
        model_name = getattr(app, "current_model", None) or "Assistant"
        sender_label = Gtk.Label(label=model_name)
        sender_label.add_css_class("bubble-model-label")
        
    sender_label.set_xalign(0.0)
    header.append(sender_label)
    header.append(Gtk.Box(hexpand=True))
    
    if text:
        copy_btn = Gtk.Button.new_from_icon_name("edit-copy-symbolic")
        copy_btn.add_css_class("flat")
        copy_btn.add_css_class("bubble-action-btn")
        copy_btn.set_tooltip_text("Copy Response" if not is_user else "Copy Message")
        copy_btn.connect("clicked", lambda b: copy_to_clipboard(text))
        header.append(copy_btn)
        
    bubble_box.append(header)
    
    # process attachments
    att_list = []
    if attachments:
        if isinstance(attachments, str):
            att_list = [{"path": attachments, "type": "image"}]
        elif isinstance(attachments, list):
            att_list = attachments

    # render image attachments
    for att in att_list:
        if isinstance(att, dict) and att.get("type") == "image":
            path = att.get("path")
            if path:
                try:
                    texture = Gdk.Texture.new_from_filename(path)
                    img = Gtk.Image.new_from_paintable(texture)
                    img.set_pixel_size(240)
                    img.add_css_class("rounded-image")
                    bubble_box.append(img)
                except Exception as e:
                    logging.error(f"Failed to load image {path}: {e}")
                    img = Gtk.Image.new_from_icon_name("image-missing-symbolic")
                    img.set_pixel_size(64)
                    bubble_box.append(img)
        
    last_bubble = render_message_chunks(app, bubble_box, text)
            
    # build avatar box
    avatar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    avatar_box.add_css_class("avatar-box")
    avatar_box.set_size_request(32, 32)
    avatar_box.set_halign(Gtk.Align.CENTER)
    avatar_box.set_valign(Gtk.Align.START) # align avatar to top
    
    if is_user:
        avatar_box.add_css_class("avatar-user")
        avatar_img = Gtk.Image.new_from_icon_name("avatar-default-symbolic")
    else:
        # load custom avatar based on model name
        model_name = getattr(app, "current_model", None) or "Assistant"
        
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_file = utils.get_model_logo_file(model_name)
        
        if img_file:
            img_path = os.path.join(base_dir, "assets", img_file)
            if os.path.exists(img_path):
                avatar_img = Gtk.Image.new_from_file(img_path)
                avatar_img.set_pixel_size(32) # scale to fit
            else:
                avatar_img = Gtk.Image.new_from_icon_name("computer-symbolic")
        else:
            avatar_img = Gtk.Image.new_from_icon_name("computer-symbolic")
        
    avatar_img.set_halign(Gtk.Align.CENTER)
    avatar_img.set_valign(Gtk.Align.CENTER)
    avatar_img.set_hexpand(True)
    avatar_img.set_vexpand(True)
    avatar_box.append(avatar_img)
    
    # arrange layout based on sender
    align = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    if is_user:
        align.set_halign(Gtk.Align.END)
        align.append(bubble_box)
        align.append(avatar_box)
    else:
        align.set_halign(Gtk.Align.START)
        align.append(avatar_box)
        align.append(bubble_box)
        
    app.chat_box.append(align)
    GLib.idle_add(scroll_to_bottom, app)
    return last_bubble

def copy_to_clipboard(text: str) -> None:
    # copy message text to clipboard
    clipboard = Gdk.Display.get_default().get_clipboard()
    content = Gdk.ContentProvider.new_for_value(text)
    clipboard.set_content(content)

def add_system_message(app, text: str) -> None:
    # insert status line in chat
    label = Gtk.Label(label=text)
    label.add_css_class("system-status")
    label.set_margin_top(10)
    label.set_margin_bottom(10)
    app.chat_box.append(label)
    app.status_labels.append(label)
    GLib.idle_add(scroll_to_bottom, app)

def add_spinner(app) -> Gtk.Spinner:
    # show thinking spinner
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)
    spinner = Gtk.Spinner()
    spinner.set_spinning(True)
    box.append(spinner)
    box.append(Gtk.Label(label="Thinking..."))
    app.chat_box.append(box)
    return box

def clear_status_labels(app) -> bool:
    # clean up status labels
    for label in app.status_labels:
        if label.get_parent() == app.chat_box:
            app.chat_box.remove(label)
    app.status_labels = []
    return False

def scroll_to_bottom(app) -> None:
    # scroll to bottom
    adj = app.scrolled.get_vadjustment()
    adj.set_value(adj.get_upper() - adj.get_page_size())

def chat_box_remove_all(app) -> None:
    # clear chat flow list
    child = app.chat_box.get_first_child()
    while child:
        app.chat_box.remove(child)
        child = app.chat_box.get_first_child()

def cancel_ai_task(app) -> None:
    # cancel active AI task cooperatively
    if app.ai_task and not app.ai_task.done():
        app.ai_task.cancel()

def update_thumbnail(app) -> None:
    # sync compose box attachment thumbnails
    child = app.thumb_box.get_first_child()
    while child:
        app.thumb_box.remove(child)
        child = app.thumb_box.get_first_child()

    if not hasattr(app, "selected_attachments") or not app.selected_attachments:
        app.thumb_box.set_visible(False)
        return

    app.thumb_box.set_visible(True)
    
    for i, att in enumerate(app.selected_attachments):
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card_box.add_css_class("thumbnail-container")
        card_box.set_size_request(80, 95)
        
        overlay = Gtk.Overlay()
        overlay.set_halign(Gtk.Align.CENTER)
        overlay.set_valign(Gtk.Align.CENTER)
        
        if att["type"] == "image":
            try:
                texture = Gdk.Texture.new_from_filename(att["path"])
                img = Gtk.Image.new_from_paintable(texture)
                img.set_pixel_size(64)
                img.add_css_class("rounded-image-thumbnail")
            except Exception as e:
                logging.error(f"Failed to load thumbnail for {att['path']}: {e}")
                img = Gtk.Image.new_from_icon_name("image-missing-symbolic")
                img.set_pixel_size(64)
                img.add_css_class("rounded-image-thumbnail")
        else:
            img = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
            img.set_pixel_size(64)
            img.add_css_class("rounded-file-thumbnail")
            
        overlay.set_child(img)
        
        remove_btn = Gtk.Button(icon_name="window-close-symbolic")
        remove_btn.add_css_class("flat")
        remove_btn.add_css_class("remove-attachment-btn")
        remove_btn.set_halign(Gtk.Align.END)
        remove_btn.set_valign(Gtk.Align.START)
        
        remove_btn.connect("clicked", lambda b, idx=i: on_remove_attachment(app, idx))
        overlay.add_overlay(remove_btn)
        
        card_box.append(overlay)
        
        name_label = Gtk.Label(label=att["name"])
        name_label.set_halign(Gtk.Align.CENTER)
        name_label.set_max_width_chars(12)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.add_css_class("caption")
        card_box.append(name_label)
        
        app.thumb_box.append(card_box)

def on_remove_attachment(app, index: int) -> None:
    # remove attachment by index
    if hasattr(app, "selected_attachments") and 0 <= index < len(app.selected_attachments):
        app.selected_attachments.pop(index)
    update_thumbnail(app)

def on_remove_thumbnail(app) -> None:
    # purge attachments
    app.selected_attachments = []
    update_thumbnail(app)
