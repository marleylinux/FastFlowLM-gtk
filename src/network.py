# network
import json
import logging
import utils
from gi.repository import Soup, GLib, Gio
from typing import List

async def _read_stream_bytes(stream, max_bytes: int = 8192) -> bytes:
    """Read up to max_bytes from a GInputStream, returning bytes."""
    data = bytearray()
    buf = bytearray(4096)
    try:
        while len(data) < max_bytes:
            n = await utils.gio_async(stream, "read_async", buf, GLib.PRIORITY_DEFAULT, None)
            if n <= 0:
                break
            data.extend(buf[:n])
    except Exception:
        pass
    return bytes(data)

async def get_ai_response(app, bubble, thinking_label, messages: List[dict]):
    # standard openai-like stream request payload
    payload = {
        "model": app.current_model,
        "messages": messages,
        "stream": True
    }
    
    if hasattr(app, "temperature") and app.temperature is not None:
        payload["temperature"] = app.temperature
    
    # retry loop because the local server takes its sweet time waking up
    for attempt in range(5):
        try:
            msg = Soup.Message.new("POST", f"{app.BASE_URL}/chat/completions")
            msg.set_request_body_from_bytes("application/json", GLib.Bytes.new(json.dumps(payload).encode()))
            
            stream = await utils.gio_async(app.session, "send_async", msg, GLib.PRIORITY_DEFAULT, None)
            
            status = msg.get_status()
            if status == Soup.Status.OK:
                return stream
            
            # libsoup3 streams the body via GInputStream — read it before closing
            response_body = b""
            if stream:
                try:
                    response_body = await _read_stream_bytes(stream)
                except Exception:
                    pass
                try:
                    stream.close(None)
                except Exception:
                    pass
            
            if response_body:
                try:
                    err_data = json.loads(response_body.decode("utf-8"))
                    if "error" in err_data and "message" in err_data["error"]:
                        raise RuntimeError(err_data["error"]["message"])
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            logging.warning(f"Server returned status {status} on attempt {attempt + 1}. Body: {response_body[:200]}")
            # server errored, no point in retrying
            if status != Soup.Status.NONE and status < 500:
                if status == Soup.Status.BAD_REQUEST:
                    raise RuntimeError("Bad Request (Status 400). Payload may be too large or malformed.")
                break
                
        except RuntimeError:
            raise
        except Exception as e:
            logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
            
        if attempt < 4:
            import asyncio
            await asyncio.sleep(1.5)
            
    return None
