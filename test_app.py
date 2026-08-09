import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = r"C:\Users\Aryan Sonsurkar\OneDrive\Documents\GitHub\Fixly-Desktop"
BACKEND_DIR = os.path.join(ROOT, "apps", "backend")
DESKTOP_DIR = os.path.join(ROOT, "apps", "desktop")
ENV_FILE = os.path.join(BACKEND_DIR, ".env.default")

env = dict(os.environ)
env["FIXLY_ENV_FILE"] = ENV_FILE
env["PYTHONUNBUFFERED"] = "1"
env["VITE_API_URL"] = "http://localhost:8000"

print("Starting backend...", flush=True)
backend = subprocess.Popen(
    [sys.executable, os.path.join(BACKEND_DIR, "run_backend.py")],
    cwd=BACKEND_DIR,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

port = None
deadline = time.time() + 30
while time.time() < deadline:
    line = backend.stdout.readline()
    if not line:
        if backend.poll() is not None:
            print("Backend exited early", flush=True)
            sys.exit(1)
        continue
    line = line.strip()
    print(f"  backend> {line}", flush=True)
    if line.startswith("FIXLY_PORT:"):
        port = int(line.split(":")[1])
        break

if not port:
    print("No port detected", flush=True)
    backend.kill()
    sys.exit(1)

print(f"Backend running on http://localhost:{port}", flush=True)

print("Starting frontend dev server...", flush=True)
BUTTON = os.path.join(DESKTOP_DIR, "node_modules", "vite", "bin", "vite.js")
frontend = subprocess.Popen(
    ["node", BUTTON, "--port", "1420"],
    cwd=DESKTOP_DIR,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

time.sleep(3)
url = "http://localhost:1420"
print(f"Opening {url}", flush=True)
webbrowser.open(url)

print("\nPress Ctrl+C to stop both servers", flush=True)
try:
    while True:
        if backend.poll() is not None:
            print("Backend stopped", flush=True)
            break
        if frontend.poll() is not None:
            print("Frontend stopped", flush=True)
            break
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...", flush=True)

backend.kill()
frontend.kill()
print("Done", flush=True)