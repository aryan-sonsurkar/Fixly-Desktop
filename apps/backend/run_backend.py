import argparse
import os
import socket
import sys

from app.main import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", type=int, default=0)
    parser.add_argument("--env-file", "-e", default="")
    args = parser.parse_args()

    if args.env_file:
        os.environ["FIXLY_ENV_FILE"] = args.env_file

    port = args.port
    if port == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    print(f"FIXLY_PORT:{port}", flush=True)

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
