"""PlantPulse Production Server Launcher with automatic browser opener and port conflict resolution."""
import os
import sys
import time
import socket
import threading
import urllib.request
import webbrowser
import subprocess
import uvicorn

PORT = 8000
URL = f"http://127.0.0.1:{PORT}"

def is_plantpulse_healthy() -> bool:
    try:
        req = urllib.request.Request(f"{URL}/health", headers={"User-Agent": "PlantPulse-Launcher"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def clean_stale_port(port: int):
    """Terminates any stale process occupying the target port if not responsive."""
    try:
        cmd = f'powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
        out = subprocess.check_output(cmd, shell=True, text=True).strip()
        if out:
            current_pid = os.getpid()
            for pid_str in out.splitlines():
                pid_str = pid_str.strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid > 0 and pid != current_pid:
                        print(f"[CLEANUP] Releasing port {port} from stale PID {pid}...", flush=True)
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
            time.sleep(1)
    except Exception:
        pass

def launch_browser():
    """Waits for server to become responsive, then opens the user's default browser."""
    print("[LAUNCHER] Waiting for server startup to open browser...", flush=True)
    opened = False
    for attempt in range(40):  # up to 20 seconds
        time.sleep(0.5)
        if is_plantpulse_healthy():
            print(f"\n[OK] PlantPulse is LIVE at {URL}")
            print("[OK] Opening web browser now...\n", flush=True)
            webbrowser.open(URL)
            opened = True
            break
    if not opened:
        # Fallback open in case health check was blocked
        print(f"[INFO] Opening browser at {URL}...", flush=True)
        webbrowser.open(URL)

if __name__ == "__main__":
    # Ensure working directory is backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)

    # 1. Check if PlantPulse is ALREADY running
    if is_plantpulse_healthy():
        print("======================================================================")
        print("  PLANTPULSE - Intelligent Industrial Energy Optimisation")
        print("======================================================================")
        print(f"[INFO] PlantPulse is ALREADY running and healthy at {URL}!")
        print("[INFO] Opening your web browser now...\n")
        webbrowser.open(URL)
        print("Press any key or close this window.")
        sys.exit(0)

    # 2. If port is in use by a stale unresponsive process, clean it up
    if is_port_in_use(PORT):
        print(f"[WARNING] Port {PORT} is currently occupied by an unresponsive process.")
        clean_stale_port(PORT)

    # 3. Start background thread to open browser when server is verified ready
    browser_thread = threading.Thread(target=launch_browser, daemon=True)
    browser_thread.start()

    # 4. Start uvicorn ASGI server
    print(f"Starting PLANTPULSE production server on {URL} ...", flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=PORT, log_level="info")
