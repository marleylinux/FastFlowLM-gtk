# ui
import init_gi
from gi.repository import Gtk, Adw
import display

def _get_new_chat_icon() -> str:
    # choose a new chat icon
    from gi.repository import Gdk
    display_default = Gdk.Display.get_default()
    if display_default:
        icon_theme = Gtk.IconTheme.get_for_display(display_default)
        if icon_theme.has_icon("tab-new-symbolic"):
            return "tab-new-symbolic"
    return "document-new-symbolic"

def get_cpu_name() -> str:
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    name = line.split(":", 1)[1].strip()
                    # clean suffixes
                    if " w/" in name:
                        name = name.split(" w/", 1)[0]
                    if " with " in name:
                        name = name.split(" with ", 1)[0]
                    name = name.replace("Processor", "")
                    # shorten name
                    if len(name) > 35:
                        name = name[:32] + "..."
                    return name.strip()
    except Exception:
        pass
    import platform
    return platform.processor() or "AMD Ryzen AI"

def get_npu_details() -> dict:
    details = {
        "present": False,
        "name": "AMD NPU",
        "firmware": "Unknown",
        "contexts": "No active contexts",
        "columns": "8 Columns"
    }
    # Check if xrt-smi is in path
    import shutil
    import subprocess
    if not shutil.which("xrt-smi"):
        return details
        
    try:
        res = subprocess.run(["xrt-smi", "examine"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            details["present"] = True
            for line in res.stdout.splitlines():
                if "NPU Firmware Version" in line:
                    details["firmware"] = line.split(":", 1)[1].strip()
                elif "RyzenAI" in line or "npu" in line.lower():
                    # Parse device name
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 2 and "BDF" not in parts[0]:
                        details["name"] = parts[1]
                        
        res_device = subprocess.run(["xrt-smi", "examine", "-r", "all"], capture_output=True, text=True, timeout=3)
        if res_device.returncode == 0:
            stdout = res_device.stdout
            if "No hardware contexts running" in stdout:
                details["contexts"] = "Idle (0 Contexts)"
            elif "AIE Partitions" in stdout:
                details["contexts"] = "Active Contexts"
            
            for line in stdout.splitlines():
                if "Total Columns" in line:
                    details["columns"] = line.split(":", 1)[1].strip() + " Columns"
    except Exception as e:
        import logging
        logging.error(f"Error parsing NPU details: {e}")
        
    return details

def _build_monitor_card(icon_name: str, name: str, val_str: str, unit_str: str, fraction: float = 0.0) -> Gtk.Box:
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    card.add_css_class("monitor-card")
    card.set_hexpand(True)

    # Top Row: Icon + Name
    top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    top_row.set_hexpand(True)

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.add_css_class("monitor-icon")
    top_row.append(icon)

    name_lbl = Gtk.Label(label=name)
    name_lbl.add_css_class("monitor-name-label")
    name_lbl.set_halign(Gtk.Align.START)
    name_lbl.set_hexpand(True)
    top_row.append(name_lbl)

    card.append(top_row)

    # Middle Row: Big Value + unit
    val_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    val_row.set_halign(Gtk.Align.START)
    val_row.set_margin_top(8)

    val_lbl = Gtk.Label(label=val_str)
    val_lbl.add_css_class("monitor-value-label")
    val_row.append(val_lbl)

    unit_lbl = Gtk.Label(label=unit_str)
    unit_lbl.add_css_class("monitor-unit-label")
    unit_lbl.set_valign(Gtk.Align.END)
    unit_lbl.set_margin_bottom(3)
    val_row.append(unit_lbl)
    card.append(val_row)

    # progress bar
    bar = Gtk.ProgressBar()
    bar.add_css_class("usage-bar")
    bar.set_fraction(fraction)
    card.append(bar)

    # refs for updates
    card._val_lbl = val_lbl
    card._bar = bar
    card._name_lbl = name_lbl
    card._unit_lbl = unit_lbl
    card._top_row = top_row

    return card

def show_welcome_message(app):
    # welcome screen
    display.chat_box_remove_all(app)

    # lock controls
    app.model_btn.set_sensitive(False)
    app.model_btn.set_popover(None)
    app.model_btn.set_tooltip_text("Start a new chat to select a model.")

    app.set_entry_locked(True, "Start a new chat to begin")
    app.btn_send.set_sensitive(False)
    app.btn_repair.set_sensitive(False)
    app.btn_attach.set_sensitive(False)

    # dashboard container
    welcome_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    welcome_container.set_hexpand(True)
    welcome_container.set_halign(Gtk.Align.FILL)

    # hero banner
    hero_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    hero_box.add_css_class("hero-box")
    
    # status pill
    status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    status_box.set_valign(Gtk.Align.CENTER)
    status_pill = Gtk.Label(label="● System Status")
    status_pill.add_css_class("live-status-pill")
    status_box.append(status_pill)
    hero_box.append(status_box)

    # center content
    center_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    center_content.set_hexpand(True)
    center_content.set_halign(Gtk.Align.CENTER)

    hero_icon = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic")
    hero_icon.set_pixel_size(48)
    hero_icon.add_css_class("hero-icon")
    center_content.append(hero_icon)

    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    text_box.set_valign(Gtk.Align.CENTER)

    title_lbl = Gtk.Label(label="FastFlowLM Dashboard")
    title_lbl.add_css_class("hero-title")
    title_lbl.set_halign(Gtk.Align.START)
    text_box.append(title_lbl)

    subtitle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    subtitle_lbl = Gtk.Label(label="Local LLM Workspace on")
    subtitle_lbl.add_css_class("hero-subtitle")
    subtitle_box.append(subtitle_lbl)

    cpu_name = get_cpu_name()
    cpu_badge = Gtk.Label(label=cpu_name)
    cpu_badge.add_css_class("hero-cpu-badge")
    subtitle_box.append(cpu_badge)
    text_box.append(subtitle_box)
    
    center_content.append(text_box)
    hero_box.append(center_content)

    welcome_container.append(hero_box)

    # diagnostic banner
    diag_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    diag_box.add_css_class("diagnostic-row")
    diag_box.add_css_class("warning") # Default style
    diag_box.set_visible(False)

    diag_title = Gtk.Label()
    diag_title.add_css_class("diagnostic-row-title")
    diag_title.set_halign(Gtk.Align.START)
    diag_box.append(diag_title)

    diag_sub = Gtk.Label()
    diag_sub.add_css_class("diagnostic-row-subtitle")
    diag_sub.set_halign(Gtk.Align.START)
    diag_sub.set_wrap(True)
    diag_box.append(diag_sub)

    diag_fix_btn = Gtk.Button(label="Automatically Apply Fixes")
    diag_fix_btn.add_css_class("suggested-action")
    diag_fix_btn.add_css_class("pill")
    diag_fix_btn.set_halign(Gtk.Align.START)
    diag_fix_btn.set_margin_top(8)
    diag_fix_btn.set_visible(False)
    if hasattr(app, "on_apply_fixes_clicked"):
        diag_fix_btn.connect("clicked", app.on_apply_fixes_clicked)
    diag_box.append(diag_fix_btn)

    app.diagnostic_banner = diag_box
    app.diagnostic_title = diag_title
    app.diagnostic_subtitle = diag_sub
    app.diagnostic_fix_btn = diag_fix_btn
    welcome_container.append(diag_box)

    # main grid
    main_grid = Gtk.Grid()
    main_grid.set_column_homogeneous(True)
    main_grid.set_column_spacing(16)
    main_grid.set_row_spacing(16)

    # resources column
    res_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    
    # section header
    sec_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    sec_header.add_css_class("section-title-box")
    sec_icon = Gtk.Image.new_from_icon_name("drive-harddisk-symbolic")
    sec_icon.add_css_class("category-icon")
    sec_header.append(sec_icon)
    sec_lbl = Gtk.Label(label="NPU & System Resources")
    sec_lbl.add_css_class("section-title-label")
    sec_header.append(sec_lbl)
    res_box.append(sec_header)

    # cards box
    cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

    # ram card
    import psutil
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    used_gb = mem.used / (1024 ** 3)
    percent = mem.percent / 100.0

    ram_card = _build_monitor_card(
        "drive-harddisk-symbolic", 
        "System RAM", 
        f"{used_gb:.1f} / {total_gb:.1f}", 
        "GB", 
        percent
    )
    # limit badge
    top_box = ram_card.get_first_child()
    lim_lbl = Gtk.Label(label=f"{total_gb:.0f}GB Max")
    lim_lbl.add_css_class("monitor-limit-badge")
    lim_lbl.set_halign(Gtk.Align.END)
    top_box.append(lim_lbl)

    cards_box.append(ram_card)

    # npu card
    npu_card = _build_monitor_card(
        "cpu-symbolic",
        "AMD NPU",
        "Validating",
        "NPU",
        0.0
    )
    # Style NPU progress bar to show pulse
    npu_card._bar.add_css_class("low")
    
    npu_lim_lbl = Gtk.Label(label="validate")
    npu_lim_lbl.add_css_class("monitor-limit-badge")
    npu_lim_lbl.set_halign(Gtk.Align.END)
    npu_card._top_row.append(npu_lim_lbl)
    npu_card._lim_lbl = npu_lim_lbl

    cards_box.append(npu_card)
    
    res_box.append(cards_box)

    app._dashboard_cards = [ram_card, npu_card]
    app._ram_card = ram_card
    app._npu_card = npu_card

    main_grid.attach(res_box, 0, 0, 1, 1)

    # info column
    welcome_info_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    welcome_info_card.add_css_class("monitor-card")
    welcome_info_card.set_vexpand(True)
    welcome_info_card.set_hexpand(True)

    welcome_title_lbl = Gtk.Label(label="Welcome to FastFlowLM")
    welcome_title_lbl.add_css_class("section-title-label")
    welcome_title_lbl.set_halign(Gtk.Align.START)
    welcome_info_card.append(welcome_title_lbl)

    info_desc = Gtk.Label()
    info_desc.set_markup(
        "<span size='medium'>A premium native interface for local LLMs.</span>\n\n"
        "• Crafted using modern GTK 4 &amp; Libadwaita standards\n"
        "• Dynamic multi-format attachments (Images &amp; Code/Text)\n"
        "• Keyboard-driven with advanced lock integration\n"
        "• Lightweight, lightning-fast native desktop performance\n"
        "• Real-time session and chat history management"
    )
    info_desc.set_halign(Gtk.Align.START)
    info_desc.set_wrap(True)
    welcome_info_card.append(info_desc)

    action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    action_box.set_margin_top(12)
    action_box.set_halign(Gtk.Align.CENTER)

    btn_start = Gtk.Button(label="Start New Chat")
    btn_start.add_css_class("pill")
    btn_start.add_css_class("accent-btn")
    btn_start.set_halign(Gtk.Align.CENTER)
    btn_start.set_size_request(200, -1)
    btn_start.connect("clicked", lambda b: app.on_new_chat(None))
    action_box.append(btn_start)

    credits_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    credits_box.set_halign(Gtk.Align.CENTER)
    credits_box.set_margin_top(8)

    link_ui = Gtk.LinkButton(uri="https://github.com/marleylinux/FastFlowLM-gtk", label="FastFlowLM-gtk")
    link_ui.set_halign(Gtk.Align.CENTER)
    credits_box.append(link_ui)

    link_engine = Gtk.LinkButton(uri="https://github.com/FastFlowLM/FastFlowLM", label="Powered by FastFlowLM")
    link_engine.add_css_class("dim-label")
    link_engine.set_halign(Gtk.Align.CENTER)
    credits_box.append(link_engine)

    action_box.append(credits_box)
    welcome_info_card.append(action_box)

    main_grid.attach(welcome_info_card, 1, 0, 1, 1)

    welcome_container.append(main_grid)

    app.chat_box.append(welcome_container)

def build_sidebar(app) -> Adw.ToolbarView:
    # build sidebar container
    toolbar_view = Adw.ToolbarView()
    toolbar_view.add_css_class("sidebar-pane")
    
    sidebar_header = Adw.HeaderBar()
    sidebar_header.set_show_end_title_buttons(False)
    
    # new chat button
    app.btn_new = Gtk.Button(icon_name=_get_new_chat_icon())
    app.btn_new.set_tooltip_text("New Chat")
    app.btn_new.connect("clicked", app.on_new_chat)
    sidebar_header.pack_start(app.btn_new)
    
    # options button
    app.options_btn = Gtk.MenuButton(icon_name="view-more-symbolic")
    app.options_btn.set_tooltip_text("Options")
    sidebar_header.pack_end(app.options_btn)
    
    toolbar_view.add_top_bar(sidebar_header)
    
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    
    # Dashboard navigation tab
    app.nav_list = Gtk.ListBox()
    app.nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    app.nav_list.add_css_class("navigation-sidebar")
    app.nav_list.connect("row-activated", app.on_nav_row_activated)
    
    db_row = Gtk.ListBoxRow()
    db_row.row_id = "dashboard"
    
    db_main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    db_main_box.set_margin_start(10)
    db_main_box.set_margin_end(5)
    db_main_box.set_margin_top(10)
    db_main_box.set_margin_bottom(10)
    
    db_icon = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic")
    db_icon.set_pixel_size(20)
    db_icon.set_valign(Gtk.Align.CENTER)
    db_icon.set_halign(Gtk.Align.CENTER)
    db_icon.set_margin_end(6)
    
    db_txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    db_txt_box.set_hexpand(True)
    
    db_title = Gtk.Label(label="System Dashboard")
    db_title.set_halign(Gtk.Align.START)
    db_title.add_css_class("sidebar-title")
    
    db_sub = Gtk.Label(label="NPU, RAM & System Stats")
    db_sub.set_halign(Gtk.Align.START)
    db_sub.add_css_class("sidebar-subtitle")
    db_sub.add_css_class("dim-label")
    
    db_txt_box.append(db_title)
    db_txt_box.append(db_sub)
    
    db_main_box.append(db_icon)
    db_main_box.append(db_txt_box)
    
    db_row.set_child(db_main_box)
    app.nav_list.append(db_row)
    
    content_box.append(app.nav_list)

    # Search chats box (placed below the Dashboard category)
    search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    search_box.set_margin_start(16)
    search_box.set_margin_end(16)
    search_box.set_margin_bottom(12)
    search_box.set_margin_top(8)
    
    app.search_entry = Gtk.SearchEntry()
    app.search_entry.set_placeholder_text("Search chats...")
    app.search_entry.connect("search-changed", app.on_search_changed)
    search_box.append(app.search_entry)
    content_box.append(search_box)

    # Chat history sub-header
    history_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    history_label_box.set_margin_start(16)
    history_label_box.set_margin_end(16)
    history_label_box.set_margin_top(8)
    history_label_box.set_margin_bottom(4)
    
    history_label = Gtk.Label(label="Chat History")
    history_label.add_css_class("sidebar-title")
    history_label.add_css_class("dim-label")
    history_label.set_halign(Gtk.Align.START)
    history_label_box.append(history_label)
    content_box.append(history_label_box)

    app.history_list = Gtk.ListBox()
    app.history_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    app.history_list.add_css_class("navigation-sidebar")
    app.history_list.connect("row-activated", app.on_history_row_activated)
    
    sidebar_scrolled = Gtk.ScrolledWindow()
    sidebar_scrolled.set_vexpand(True)
    sidebar_scrolled.set_child(app.history_list)
    content_box.append(sidebar_scrolled)
    
    toolbar_view.set_content(content_box)
    return toolbar_view

def build_main_content(app) -> Adw.ToolbarView:
    # build main chat container
    toolbar_view = Adw.ToolbarView()
    
    app.header = Adw.HeaderBar()
    
    # sidebar toggle button
    app.btn_sidebar = Gtk.ToggleButton(icon_name="sidebar-show-symbolic")
    app.btn_sidebar.set_active(True)
    app.btn_sidebar.set_tooltip_text("Toggle Sidebar")
    app.btn_sidebar.connect("toggled", lambda b: app.split_view.set_show_sidebar(b.get_active()))
    app.header.pack_start(app.btn_sidebar)
    
    # repair model button
    app.btn_repair = Gtk.Button(icon_name="view-refresh-symbolic")
    app.btn_repair.set_tooltip_text("Repair Model")
    app.btn_repair.connect("clicked", app.on_repair_clicked)
    app.header.pack_end(app.btn_repair)

    # eject model button
    app.btn_eject = Gtk.Button(icon_name="media-eject-symbolic")
    app.btn_eject.set_tooltip_text("Eject Model")
    app.btn_eject.connect("clicked", app.on_eject_clicked)
    app.header.pack_end(app.btn_eject)
    
    # model picker popover
    app.model_btn = Gtk.MenuButton()
    app.header.set_title_widget(app.model_btn)
    
    toolbar_view.add_top_bar(app.header)
    
    # scroll container
    app.scrolled = Gtk.ScrolledWindow()
    app.scrolled.set_vexpand(True)
    app.scrolled.set_kinetic_scrolling(True)
    app.scrolled.add_css_class("chat-scroll")
    
    # clamp chat layout
    clamp_chat = Adw.Clamp()
    clamp_chat.set_maximum_size(1100)
    clamp_chat.set_tightening_threshold(800)
    
    app.chat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    app.chat_box.set_hexpand(True)
    app.chat_box.set_halign(Gtk.Align.FILL)
    app.chat_box.set_margin_top(18)
    app.chat_box.set_margin_bottom(18)
    app.chat_box.set_margin_start(16)
    app.chat_box.set_margin_end(16)
    
    clamp_chat.set_child(app.chat_box)
    app.scrolled.set_child(clamp_chat)
    toolbar_view.set_content(app.scrolled)
    
    # bottom input area
    bottom_bar_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    
    clamp_bottom = Adw.Clamp()
    clamp_bottom.set_maximum_size(1100)
    clamp_bottom.set_tightening_threshold(800)
    
    bottom_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    bottom_content.set_margin_start(16)
    bottom_content.set_margin_end(16)
    bottom_content.set_margin_bottom(16)
    bottom_content.set_margin_top(8)
    
    # attachment thumbnails
    app.thumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    app.thumb_box.set_margin_bottom(4)
    bottom_content.append(app.thumb_box)
    
    # custom text input view
    app.input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    app.input_box.add_css_class("input-area")
    
    input_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    input_container.add_css_class("input-view")
    input_container.set_hexpand(True)
    
    app.input_scroll = Gtk.ScrolledWindow()
    app.input_scroll.set_hexpand(True)
    app.input_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    app.input_scroll.set_min_content_height(36)
    app.input_scroll.set_max_content_height(150)
    
    app.entry = Gtk.TextView()
    app.entry.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    app.entry.set_accepts_tab(False)
    app.entry.set_valign(Gtk.Align.CENTER)
    
    key_ctrl = Gtk.EventControllerKey()
    key_ctrl.connect("key-pressed", app.on_key_pressed)
    app.entry.add_controller(key_ctrl)
    
    app.input_scroll.set_child(app.entry)
    input_container.append(app.input_scroll)
    
    # attachment button
    app.btn_attach = Gtk.Button(icon_name="paperclip-symbolic")
    app.btn_attach.add_css_class("flat")
    app.btn_attach.set_valign(Gtk.Align.CENTER)
    app.btn_attach.connect("clicked", app.on_attach_clicked)
    input_container.append(app.btn_attach)

    from gi.repository import Gdk
    drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
    def _handle_drop(_t, v, _x, _y):
        import handlers
        return handlers.on_files_dropped(app, v)
    drop_target.connect("drop", _handle_drop)
    input_container.add_controller(drop_target)
    
    app.input_box.append(input_container)
    
    # send button
    app.btn_send = Gtk.Button(icon_name="mail-send-symbolic")
    app.btn_send.add_css_class("circular")
    app.btn_send.add_css_class("accent-btn")
    app.btn_send.set_valign(Gtk.Align.CENTER)
    app.btn_send.connect("clicked", app.on_send)
    app.input_box.append(app.btn_send)
    
    bottom_content.append(app.input_box)
    clamp_bottom.set_child(bottom_content)
    bottom_bar_layout.append(clamp_bottom)
    
    toolbar_view.add_bottom_bar(bottom_bar_layout)
    return toolbar_view

def build_memlock_page(app) -> Adw.ToolbarView:
    toolbar = Adw.ToolbarView()

    header = Adw.HeaderBar()
    header.add_css_class("main-header")
    win_title = Adw.WindowTitle()
    win_title.set_title("FastFlowLM-gtk")
    win_title.set_subtitle("System Configuration Required")
    header.set_title_widget(win_title)
    toolbar.add_top_bar(header)

    status = Adw.StatusPage()
    status.set_icon_name("memory-symbolic")
    status.set_title("Memory Locking Required")

    import os
    conf_path = "/etc/security/limits.d/99-fastflowlm-gtk.conf"

    if os.path.exists(conf_path):
        status.set_description(
            "The installer already created the memlock configuration for you.\n\n"
            "You must restart your computer (or log out and log back in) for it to take effect.\n"
            "FastFlowLM-gtk cannot continue until unlimited memory locking is active."
        )

        btn_reboot = Gtk.Button(label="Reboot Now")
        btn_reboot.add_css_class("destructive-action")
        btn_reboot.add_css_class("pill")
        btn_reboot.set_halign(Gtk.Align.CENTER)

        def on_reboot(_b):
            import subprocess
            subprocess.run(["reboot"])

        btn_reboot.connect("clicked", on_reboot)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(btn_reboot)
        status.set_child(box)
    else:
        status.set_description(
            "Local LLMs require unlimited memory locking (memlock) to run efficiently.\n"
            "Your system currently restricts this.\n\n"
            "The installer should have already configured this for you, but a reboot may be required."
        )
        btn = Gtk.Button(label="Configure Automatically")
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_halign(Gtk.Align.CENTER)

        def on_fix(_b):
            import subprocess
            cmd = "echo '* - memlock unlimited' > /etc/security/limits.d/99-fastflowlm-gtk.conf"
            try:
                res = subprocess.run(["pkexec", "sh", "-c", cmd])
                if res.returncode == 0:
                    status.set_description(
                        "Configuration Applied!\n\n"
                        "Please restart your computer (or log out and log back in)\n"
                        "for the changes to take effect."
                    )
                    btn.set_visible(False)
                    btn_reboot_manual.set_visible(True)
            except Exception as e:
                print(e)

        btn.connect("clicked", on_fix)

        btn_reboot_manual = Gtk.Button(label="Reboot Now")
        btn_reboot_manual.add_css_class("destructive-action")
        btn_reboot_manual.add_css_class("pill")
        btn_reboot_manual.set_halign(Gtk.Align.CENTER)
        btn_reboot_manual.set_margin_top(8)

        def on_reboot_manual(_b):
            import subprocess
            subprocess.run(["reboot"])

        btn_reboot_manual.connect("clicked", on_reboot_manual)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(btn)
        box.append(btn_reboot_manual)
        status.set_child(box)

    toolbar.set_content(status)
    return toolbar
