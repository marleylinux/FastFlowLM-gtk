#!/usr/bin/env python3
import sys
import warnings
import asyncio
import init_gi  # noqa: F401
from gi.repository import GLib
from gi.events import GLibEventLoopPolicy
from main import FlmChatApp

# filter out annoying deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# set prgname so taskbar icon works
GLib.set_prgname("com.marley.FastFlowLM-gtk")
GLib.set_application_name("FastFlowLM-gtk")

# set policy for async in gtk
asyncio.set_event_loop_policy(GLibEventLoopPolicy())

if __name__ == "__main__":
    app = FlmChatApp()
    app.run(sys.argv)
