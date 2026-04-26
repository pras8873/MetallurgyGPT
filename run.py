import subprocess
import sys
import os
import webbrowser
import time

# Detect python command (python or python3)
PYTHON = sys.executable

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

print("🚀 Starting MetallurgyGPT...")

# Start backend
backend_process = subprocess.Popen(
    [PYTHON, "app.py"],
    cwd=BACKEND_DIR
)

print("✅ Backend started at http://127.0.0.1:5000")

# Start frontend server
frontend_process = subprocess.Popen(
    [PYTHON, "-m", "http.server", "5500"],
    cwd=FRONTEND_DIR
)

print("✅ Frontend started at http://127.0.0.1:5500")

# Give servers time to start
time.sleep(3)

# Open browser
webbrowser.open("http://127.0.0.1:5500")

print("🌐 Opening browser...")

try:
    backend_process.wait()
    frontend_process.wait()
except KeyboardInterrupt:
    print("\n🛑 Stopping servers...")
    backend_process.terminate()
    frontend_process.terminate()