# FastFlowLM-gtk

A minimalist desktop interface for [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM).

This application provides a simple environment for interacting with local LLMs, designed for Arch Linux users who want a distraction-free experience that integrates with the system dark mode.

## Features
- **Distraction-free interface:** Uses standard GNOME dark mode with black AI chat bubbles for clear reading.
- **Backend management:** Detects flm serve status and handles lifecycle management.
- **Session-based model loading:** Automates model loading and unloading per session to optimize resource usage.
- **History persistence:** Automatically saves chat sessions to the configuration directory, using the first prompt as the chat title.
- **Syntax highlighting:** Provides high-quality syntax highlighting for code blocks using GtkSourceView 5.
- **Minimal controls:** Includes basic session and model management without extra overhead.

## Quick Installation

This application is built for Arch Linux. The provided installer script manages system dependencies and file placement.

1. **Clone the repo:**
   ```bash
   git clone https://github.com/marleylinux/FastFlowLM-GTK
   cd FastFlowLM-GTK
   ```

2. **Run the installer:**
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

The script installs fastflowlm and all required GTK/GNOME dependencies, then sets up the application. You can find "FastFlowLM-gtk" in your application menu.
