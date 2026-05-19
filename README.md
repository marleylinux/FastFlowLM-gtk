# FastFlowLM-gtk

A minimalist desktop interface for [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM).

FastFlowLM-gtk is a lightweight, distraction-free application built with GTK 4 and Libadwaita. It serves as a dedicated interface for interacting with local LLMs, focusing on a clean, modern layout.

## Installation

### AUR (Recommended)
You can install this package using your favorite AUR helper:
```bash
yay -S fastflowlm-gtk
# OR
paru -S fastflowlm-gtk
```

### Manual Installation
If you prefer to build from source:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/marleylinux/FastFlowLM-GTK
   cd FastFlowLM-GTK
   ```

2. **Run the installer:**
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

The script installs `fastflowlm` and all required GTK dependencies, then sets up the application.

## Features
- **Distraction-free interface:** Uses modern GNOME-style design with customizable chat bubble themes.
- **Vision & File Support:** Supports image attachments (for vision-capable models) with intuitive thumbnail previews and removable attachments.
- **Thinking Indicator:** Real-time "Thinking..." status when the AI is processing requests.
- **Customizable Theming:** Change the app's global accent color to match your preference, persisting automatically across restarts.
- **Robust Session Management:** Smart chat-switching with confirmation dialogs and resource-cleanup delays to prevent connection issues.
- **History persistence:** Automatically saves chat sessions, managing local state cleanly.
- **Minimal controls:** Includes essential management without extra overhead.

## System Dependencies
The installation process ensures the following are present on your system:
- `fastflowlm`: The backend engine.
- `python`, `python-gobject`: Required for application logic and GTK bindings.
- `gtk4`, `libadwaita`: Modern UI toolkit components.
- `libsoup3`: Handles asynchronous HTTP communication.
- `gtksourceview5`: Provides professional-grade syntax highlighting.
