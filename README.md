# FastFlowLM-GTK

A minimalist, high-performance GTK 4 desktop interface for [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM).

Built for Arch Linux, this application provides a distraction-free environment for interacting with local LLMs, focusing on a "Just Talk" aesthetic with standard GNOME dark mode integration.

## Features

- **Minimalist Aesthetic:** Standard GNOME dark mode with pure black AI chat bubbles for high-contrast, distraction-free reading.
- **Smart Backend Management:** Automatically detects `flm serve` status and initializes the environment.
- **Per-Chat Model Loading:** Automates loading/unloading models per session to optimize VRAM/RAM usage.
- **Persistent History:** Automatically saves your chat sessions with smart tab titles and model metadata.
- **Professional Streaming:** Real-time word-by-word streaming with GtkSourceView 5 syntax highlighting for code blocks.
- **Management Tools:** Built-in model selector with download capability and forceful Eject button for memory management.

## Installation

### Prerequisites
- Python 3.12+
- PyGObject (GTK 4.14+, Libadwaita 1.5+)
- libsoup 3.0
- GtkSourceView 5
- `flm` (FastFlowLM)

On Arch Linux:
```bash
sudo pacman -S python python-gobject gtk4 libadwaita libsoup3 gtksourceview5
```

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/marleylinux/FastFlowLM-GTK
   cd FastFlowLM-GTK
   ```
2. Run the installer:
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```
3. Launch via your terminal as `flm-gtk` or from your application menu.
