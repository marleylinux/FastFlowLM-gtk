import subprocess
import json
import psutil
import time
import os
import logging
from typing import List, Dict, Optional

def get_all_models() -> List[Dict]:
    # fetch models from flm cli
    try:
        res = subprocess.run(["flm", "list", "--json"], 
                           capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        models = data.get("models", [])
        models.sort(key=lambda x: (not x.get('installed', False), x['model']))
        return models
    except Exception as e:
        logging.error(f"Error listing models: {e}")
        return []

def is_model_in_memory(server_process: Optional[subprocess.Popen], model_name: Optional[str] = None) -> bool:
    # check if server is running
    if server_process and server_process.poll() is None:
        return True
        
    try:
        # backup check via pgrep
        pattern = "flm serve"
        if model_name:
            pattern += f" {model_name}"
            
        result = subprocess.run(["pgrep", "-f", pattern], capture_output=True)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Error executing process tracking: {e}")
        return False

def is_port_open(port: int = 52625) -> bool:
    # check if port is listening
    import socket
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.1):
            return True
    except Exception:
        return False

def is_server_ready(model_name: str, port: int = 52625, server_process=None) -> bool:
    # verify server is ready
    # check process first
    if server_process and server_process.poll() is None:
        return is_port_open(port)
    # check port next
    return is_model_in_memory(None, model_name) and is_port_open(port)

def kill_existing_servers():
    # kill orphaned instances because pkill is a mess
    try:
        subprocess.run(["pkill", "-f", "flm serve"], stderr=subprocess.DEVNULL)
    except Exception:
        pass

def has_sufficient_ram(required_gb=4.0) -> bool:
    # check memory before doing something dumb
    try:
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024 ** 3)
        return available_gb >= required_gb
    except Exception as e:
        logging.error(f"RAM evaluation failed: {e}")
        return True  # hope for the best if psutil fails

def start_flm_serve(model: str, current_server_process: Optional[subprocess.Popen], pmode: str = "performance", ctx_len: int = 2048) -> subprocess.Popen:
    # terminate existing process asynchronously
    if current_server_process:
        def reap_process(proc):
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    pass
            except Exception:
                pass
        
        import threading
        threading.Thread(target=reap_process, args=(current_server_process,), daemon=True).start()
            
    # sweep leftover processes running on our default port
    kill_existing_servers()
    
    log_path = os.path.expanduser("~/.config/flm/server.log")
    log_file = subprocess.DEVNULL
    try:
        f = open(log_path, "a")
        f.write(f"\n--- Starting {model} at {time.ctime()} ---\n")
        f.flush()
        log_file = f
    except Exception:
        pass

    cmd = ["flm", "serve", model]
    if pmode:
        cmd.extend(["--pmode", pmode])
    if ctx_len and ctx_len > 0:
        cmd.extend(["--ctx-len", str(ctx_len)])

    proc = subprocess.Popen(cmd, 
                             stdout=log_file, 
                             stderr=log_file)
                             
    if log_file != subprocess.DEVNULL:
        log_file.close()
        
    return proc
