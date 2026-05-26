# FastFlowLM-gtk

GTK4 chat app for FastFlowLM. Runs local models without Electron eating all your RAM.

I put it together because I wanted something that felt normal on a Linux desktop.

## What it does

- Download and switch between local models from inside the app
- Drag and drop images for vision models
- Syntax highlighting for code (Python, C++, bash, etc) using real GtkSourceView
- Chat history with search and the ability to favourite chats
- NPU dashboard that shows if your stuff is actually working and checks memlock
- Keyboard shortcuts for the usual things (new chat, search, copy last answer, sidebar toggle)
- Warns you if a model is probably too big for your system

## Memory locking (memlock)

Big models need to be locked in RAM. The install script and AUR package add the right limits.d file for you.

After installing you **have** to log out and back in (or reboot) or the app will block you. It tells you this.

## Requirements (Arch)

```bash
sudo pacman -S gtk4 libadwaita gtksourceview5 libsoup3 python-gobject python-psutil fastflowlm xrt-plugin-amdxdna
```

## Install

**From the AUR (recommended):**

```bash
yay -S fastflowlm-gtk
```

**Manual:**

```bash
git clone https://github.com/marleylinux/FastFlowLM-gtk
cd FastFlowLM-gtk
sudo ./install.sh
```

After that it should show up in your menu as FastFlowLM-gtk.

## Running without installing (for testing)

```bash
python3 src/app.py
```

## Shortcuts

- Ctrl+N → new chat
- Ctrl+F → search history
- F9 → toggle sidebar
- Ctrl+Shift+C → copy last response
- Ctrl+? or Ctrl+/ → show shortcuts
- Enter → send
- Shift+Enter → newline

## Uninstall

```bash
sudo ./uninstall.sh
```

It also removes the memlock config it added.

## License

MIT
