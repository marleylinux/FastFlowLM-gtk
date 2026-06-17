<p align="center">
  <img src="src/assets/com.marley.FastFlowLM-gtk.png" width="128" height="128" alt="FastFlowLM-gtk logo" />
</p>

# FastFlowLM-gtk

GTK4 chat app for FastFlowLM. Runs local models without Electron eating all your RAM.

Powered by [FastFlowLM](https://github.com/FastFlowLM/FastFlowLM) ❤️

![FastFlowLM-gtk Demo](fastflowlm.gif)

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

## Requirements

- Python 3.11+
- gtk4 + libadwaita + python-gobject
- gtksourceview5 + libsoup3 + python-psutil
- fastflowlm + xrt-plugin-amdxdna

## Install

**Arch (easiest):**

```bash
yay -S fastflowlm-gtk
```

Or build from this repo:

```bash
git clone https://github.com/marleylinux/FastFlowLM-gtk
```
```bash
cd FastFlowLM-gtk
makepkg -si
```

**Other distros:**

```bash
git clone https://github.com/marleylinux/FastFlowLM-gtk
```
```bash
cd FastFlowLM-gtk
sudo ./install.sh
```

Then launch "FastFlowLM-gtk" from your menu or just run `fastflowlm-gtk`.

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

---

### Check out my other apps:

| [<img src="https://raw.githubusercontent.com/marleylinux/cpupower-gtk/main/src/assets/com.marley.cpupower-gtk.png" width="48" height="48" /><br/>cpupower-gtk](https://github.com/marleylinux/cpupower-gtk) | [<img src="https://raw.githubusercontent.com/marleylinux/Ryzenadj-gtk/main/src/assets/com.marley.ryzenadj-gtk.png" width="48" height="48" /><br/>Ryzenadj-gtk](https://github.com/marleylinux/Ryzenadj-gtk) | [<img src="https://raw.githubusercontent.com/marleylinux/FastFlowLM-gtk/main/src/assets/com.marley.FastFlowLM-gtk.png" width="48" height="48" /><br/>FastFlowLM-gtk](https://github.com/marleylinux/FastFlowLM-gtk) | [<img src="https://raw.githubusercontent.com/marleylinux/fetch-gtk/main/src/assets/com.marley.fetch-gtk.png" width="48" height="48" /><br/>fetch-gtk](https://github.com/marleylinux/fetch-gtk) |
|---|---|---|---|
