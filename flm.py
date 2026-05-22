import subprocess
import json
import psutil
import time
import os
from typing import List, Dict, Optional

def get_all_models() -> List[Dict]:
    # let's fetch the list of models by calling the flm command line tool
    try:
        res = subprocess.run(["flm", "list", "--json"], 
                           capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        models = data.get("models", [])
        models.sort(key=lambda x: (not x.get('installed', False), x['model']))
        return models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def is_model_in_memory(server_process: Optional[subprocess.Popen], model_name: Optional[str] = None) -> bool:
    # let's see if our model server is active right now
    if server_process and server_process.poll() is None:
        return True
        
    try:
        # fallback to using pgrep if the subprocess handle isn't available
        pattern = "flm serve"
        if model_name:
            pattern += f" {model_name}"
            
        result = subprocess.run(["pgrep", "-f", pattern], capture_output=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error executing process tracking: {e}")
        return False

def is_port_open(port: int = 52625) -> bool:
    # see if the model server port is open and listening
    import socket
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.1):
            return True
    except:
        return False

def is_server_ready(model_name: str, port: int = 52625, server_process=None) -> bool:
    # checks to see if the server is fully ready to receive chat messages
    # check the active process first
    if server_process and server_process.poll() is None:
        return is_port_open(port)
    # then check the network port
    return is_model_in_memory(None, model_name) and is_port_open(port)

def kill_existing_servers():
    # clean up any running server processes before starting a new one
    try:
        subprocess.run(["pkill", "-f", "flm serve"], stderr=subprocess.DEVNULL)
    except:
        pass

def has_sufficient_ram(required_gb=4.0) -> bool:
    # check if the system has enough free memory to run the model
    try:
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024 ** 3)
        return available_gb >= required_gb
    except Exception as e:
        print(f"RAM evaluation failed: {e}")
        return True  # if we can't check, we'll assume it's fine and hope for the best

def start_flm_serve(model: str, current_server_process: Optional[subprocess.Popen]) -> subprocess.Popen:
    # terminate the active server to swap in the new one
    if current_server_process:
        current_server_process.terminate()
        try:
            current_server_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            current_server_process.kill()
            
    # sweep away any leftover server processes to free up RAM
    kill_existing_servers()
    
    log_path = os.path.expanduser("~/.config/flm/server.log")
    log_file = subprocess.DEVNULL
    try:
        f = open(log_path, "a")
        f.write(f"\n--- Starting {model} at {time.ctime()} ---\n")
        f.flush()
        log_file = f
    except:
        pass

    return subprocess.Popen(["flm", "serve", model], 
                             stdout=log_file, 
                             stderr=log_file)
