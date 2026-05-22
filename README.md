# FastFlowLM-gtk

A native GTK4 chat client for [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM).

I'm a hobbyist coder who loves desktop Linux, and I built this because I wanted something that actually felt like it belonged on my desktop. I got tired of web UIs and heavy Electron apps eating up my RAM just to talk to a local model. This is a simple, lightweight GTK4 app that works nicely with GNOME and tiling window managers.

This is a personal hobby project I wrote just for the fun of it. There are no tracking scripts, no telemetry, and no bloated web frameworks here—just a pure local desktop tool.

---

## Things I Built It to Do

*   **Super Fast Model Swapping** – You can download, load, and switch models directly in the app without touching the terminal.
*   **Real Syntax Highlighting** – Powered by `GtkSourceView 5` so code blocks actually look good (supporting Python, C++, JS, Bash, and more).
*   **Vision/Image Support** – If you are running a vision model (VLM), you can drag and drop images directly into the chat.
*   **Completely Offline & Local** – Everything stays on your machine, exactly as it should be.
*   **Keyboard Shortcuts** – Built for people who prefer using the keyboard instead of clicking around.
*   **RAM Safety** – It shows a friendly warning before loading a model that might freeze your system if you're low on RAM.

---

## Keyboard Shortcuts

Here are the shortcuts I set up to make navigation quick and easy:

| Shortcut | Action |
| :--- | :--- |
| **Ctrl + N** | Start a new chat session |
| **Ctrl + F** | Search through chat history |
| **F9** | Toggle the sidebar display |
| **Ctrl + Shift + C** | Copy the last assistant response to your clipboard |
| **Ctrl + ?** or **Ctrl + /** | Show the shortcut helper dialog |
| **Enter** | Send your message |
| **Shift + Enter** | Insert a new line in the text box |

---

## Performance Tip: Memory Locking (memlock)

To get the absolute best performance out of local LLMs, you'll want to enable memory locking (`memlock`). By default, Linux might swap parts of your active model out of RAM and onto your disk, which makes responses super slow. Memory locking forces your system to keep the model pinned in RAM.

Here is how you can set it up:

1. Open `/etc/security/limits.conf` in your favorite editor (you'll need `sudo`):
   ```bash
   sudo nano /etc/security/limits.conf
   ```
2. Add these two lines at the bottom of the file (replace `your-username` with your actual Linux username, like `marley`):
   ```text
   your-username    soft    memlock    unlimited
   your-username    hard    memlock    unlimited
   ```
3. Log out of your desktop session and log back in (or restart) for the new limits to take effect.

Once configured, your local model server will run noticeably faster and smoother!

---

## Getting Started (Arch Linux)

Since I run Arch, I packaged it for Pacman and the AUR. You'll need `fastflowlm` installed on your system.

### 1. Grab dependencies via Pacman:
```bash
sudo pacman -S gtk4 libadwaita gtksourceview5 libsoup3 python-gobject python-psutil fastflowlm xrt-plugin-amdxdna
```

### 2. Install from the AUR:
```bash
yay -S fastflowlm-gtk
```

### 3. Or install manually:
If you prefer to clone and run the installation script:
```bash
git clone https://github.com/marleylinux/FastFlowLM-gtk
cd FastFlowLM-gtk
sudo ./install.sh
```

### Running Directly
If you want to run it directly from the source directory without installing it globally:
```bash
python app.py
```
