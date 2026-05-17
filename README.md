# FastFlowLM-gtk

A minimalist desktop interface for [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM).

FastFlowLM-gtk is a lightweight, distraction-free application built with GTK 4 and Libadwaita. It serves as a dedicated interface for interacting with local LLMs, focusing on a clean, simple layout.

## What this application does
- **Backend Lifecycle Management:** Automatically detects, starts, and stops the `flm serve` process. It dynamically loads/unloads models to manage VRAM/RAM usage effectively, resolving common connection issues.
- **Model Interaction:** Provides a direct interface to chat with locally-hosted models using an OpenAI-compatible API.
- **Session Management:** Automatically saves your chat history to `~/.config/flm/history/`, allowing you to resume past conversations.
- **Smart Formatting:** Uses GtkSourceView 5 for high-quality syntax highlighting of code blocks and provides support for bold text and inline code formatting.
- **Resource Management:** Includes a forceful "Eject" command to terminate background processes and free system resources immediately.

## Quick Installation

This application is packaged for Arch Linux. The provided installer script automatically handles the installation of all system dependencies.

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

### System Dependencies Installed
The installer script runs `pacman` to ensure your system has the following components:
- `fastflowlm`: The backend engine required to run the local LLM server.
- `python`, `python-gobject`: Required to run the application logic and GTK bindings.
- `gtk4`, `libadwaita`: The modern UI toolkit for the application window and controls.
- `libsoup3`: Handles asynchronous HTTP communication with the local LLM server.
- `gtksourceview5`: Provides professional-grade syntax highlighting for code blocks.

Once installed, you can launch **FastFlowLM-gtk** from your application launcher.
