#!/usr/bin/env python3
import sys
import warnings
# let's filter out warnings to keep the console clean
warnings.filterwarnings("ignore", category=DeprecationWarning)
import asyncio
import init_gi
from gi.repository import Gio, GLib
from gi.events import GLibEventLoopPolicy
from main import FlmChatApp

# giving the app a proper name so the taskbar icon displays correctly
GLib.set_prgname("com.marley.FastFlowLM-gtk")
GLib.set_application_name("FastFlowLM-gtk")

# set up the event loop policy before running any background tasks
asyncio.set_event_loop_policy(GLibEventLoopPolicy())

if __name__ == "__main__":
    app = FlmChatApp()
    app.run(sys.argv)
