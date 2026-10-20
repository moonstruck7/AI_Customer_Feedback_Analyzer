"""
Convenience launcher for AI Customer Feedback Analyzer
Starts the FastAPI server with Uvicorn and launches the browser
"""
import sys
import socket
import uvicorn
from app.main import app

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

if __name__ == "__main__":
    print("=" * 60)
    print("  AI Customer Feedback Analyzer")
    print("  Third-Year Computer Engineering Diploma Project (MSBTE)")
    print("=" * 60)

    target_port = 8000
    if is_port_in_use(target_port):
        print(f"[!] Notice: Port {target_port} is already in use by another instance.")
        target_port = 8001
        print(f"[*] Starting on fallback port {target_port} ...")

    print(f"Starting FastAPI Application on http://127.0.0.1:{target_port} ...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=target_port, reload=False)
