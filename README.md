# FastFlowLM-gtk

A simple, fast, and native GTK 4 interface for the [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM) engine.

I built this because I wanted a clean, distraction-free way to chat with local LLMs on my Arch Linux setup, without all the overhead of electron apps or web browsers. It's designed to be light, stay out of your way, and run great on GTK/Libadwaita.

## What it does

### Chatting
* **Stays in sync:** Handles message serialization so you don't break your session while it's thinking.
* **Smart focus:** The cursor snaps back to your input bar automatically when the AI is done.
* **Rate-limiting:** Keeps things steady if your backend needs a breather.
* **Vision:** Drag and drop (or attach) images if your model supports it.
* **Formatting:** Renders Markdown (bolding, code blocks, etc.) properly in the chat.

### Sessions
* **History:** Saves your chats automatically to `~/.config/flm/history`.
* **Sidebar:** A searchable sidebar for finding old thoughts.
* **Control:** Delete or clear chats easily.

### System stuff
* **Model Picker:** Swap between models on the fly.
* **Installer:** Download models right inside the app.
* **Theming:** Match your accent color to your system theme.
* **Memory Safety:** It checks your RAM before trying to load a massive model to stop it from freezing your system.

## How it's built
I modularized the code so it’s actually fun to work on. It’s a clean controller-service setup, even though it all lives in one flat directory for my build scripts:
- `main.py`: The main controller that glues everything together.
- `ui.py`: Builds the window and widgets.
- `display.py`: Handles the chat bubbles and UI updates.
- `sessions.py`: Saves/loads your chat history.
- `network.py`: Talks to the AI server.
- `models.py`: Manages the local model files and server processes.
- `theme.py`: Handles the CSS colors.
- `handlers.py`: Manages button clicks and key presses.

## Installation

### Arch Linux (AUR)
If you're on Arch, just use your favorite AUR helper:
```bash
yay -S fastflowlm-gtk
```

### Manual
1. Clone it:
   ```bash
   git clone https://github.com/marleylinux/FastFlowLM-gtk
   cd FastFlowLM-gtk
   ```

2. Install with the script:
   ```bash
   sudo ./install.sh
   ```

---
*Powered by [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM).* << (made by people way smarter than me)
*Contact: warburtonmarley@proton.me*
