import os
import re
import subprocess
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "apps", "backend")
DESKTOP_DIR = os.path.join(ROOT, "apps", "desktop")
ENV_FILE = os.path.join(BACKEND_DIR, ".env.default")
PID_FILE = os.path.join(ROOT, ".test_app.pids")

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clean(line: str) -> str:
    return ANSI_RE.sub("", line)


def taskkill_tree(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
    )


def kill_stale_servers() -> None:
    found = []
    if os.path.exists(PID_FILE):
        try:
            raw = open(PID_FILE).read().strip()
            found = [int(p) for p in raw.split(",") if p.strip().isdigit()]
        except Exception:
            pass
    for pid in found:
        taskkill_tree(pid)
    if found:
        print("Cleaned up previous test servers", flush=True)
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    if not found:
        print("(no previous servers to clean up)", flush=True)


def start_reader(proc: subprocess.Popen, prefix: str) -> threading.Thread:
    def _read():
        for line in proc.stdout:
            line = clean(line).rstrip()
            if line:
                print(f"  {prefix}> {line}", flush=True)

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    return t


def main() -> None:
    kill_stale_servers()

    env = dict(os.environ)
    env["FIXLY_ENV_FILE"] = ENV_FILE
    env["PYTHONUNBUFFERED"] = "1"

    # Backend on a random free port (0) so port conflicts never happen.
    print("Starting backend...", flush=True)
    backend = subprocess.Popen(
        [sys.executable, os.path.join(BACKEND_DIR, "run_backend.py"), "0"],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    backend_port = None
    deadline = time.time() + 30
    while time.time() < deadline:
        if backend.poll() is not None:
            print("Backend exited immediately - see output above", flush=True)
            sys.exit(1)
        line = backend.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        line = clean(line).rstrip()
        print(f"  backend> {line}", flush=True)
        m = re.match(r"^FIXLY_PORT:(\d+)$", line)
        if m:
            backend_port = int(m.group(1))
            break

    if not backend_port:
        print("Backend did not report a port", flush=True)
        taskkill_tree(backend.pid)
        sys.exit(1)

    print(f"Backend running on http://localhost:{backend_port}", flush=True)
    start_reader(backend, "backend")

    env["VITE_API_URL"] = f"http://localhost:{backend_port}"

    print("Starting frontend dev server...", flush=True)
    VITE = os.path.join(DESKTOP_DIR, "node_modules", "vite", "bin", "vite.js")
    frontend = subprocess.Popen(
        ["node", VITE, "--port", "1420", "--strictPort", "false"],
        cwd=DESKTOP_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    frontend_url = None
    deadline = time.time() + 30
    while time.time() < deadline:
        if frontend.poll() is not None:
            print("Frontend exited immediately - see output above", flush=True)
            taskkill_tree(backend.pid)
            sys.exit(1)
        line = frontend.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        line = clean(line).rstrip()
        print(f"  frontend> {line}", flush=True)
        m = re.search(r"Local:\s+(http://\S+)", line)
        if m:
            frontend_url = m.group(1).strip()
            break

    if not frontend_url:
        print("Could not determine frontend URL", flush=True)
        taskkill_tree(backend.pid)
        taskkill_tree(frontend.pid)
        sys.exit(1)

    start_reader(frontend, "frontend")
    print(f"Opening {frontend_url}", flush=True)
    time.sleep(1)
    webbrowser.open(frontend_url)

    with open(PID_FILE, "w") as f:
        f.write(f"{backend.pid},{frontend.pid}")

    print("\nTesting! Press Ctrl+C to stop both servers.\n", flush=True)
    try:
        while True:
            if backend.poll() is not None:
                print("Backend stopped unexpectedly", flush=True)
                break
            if frontend.poll() is not None:
                print("Frontend stopped unexpectedly", flush=True)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...", flush=True)

    taskkill_tree(backend.pid)
    taskkill_tree(frontend.pid)
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    print("Done", flush=True)


if __name__ == "__main__":
    main()