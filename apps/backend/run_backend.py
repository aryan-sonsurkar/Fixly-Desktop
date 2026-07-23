import socket
import sys

from app.main import app

if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if port == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    print(f"FIXLY_PORT:{port}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
