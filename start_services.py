#!/usr/bin/env python3
"""
Start script for the LangGraph Data Analysis Copilot.

This script starts both the FastAPI server and Streamlit UI with proper port management.
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def find_free_port(start_port=8000):
    """Find a free port starting from the given port."""
    import socket
    
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports found")

def start_api_server():
    """Start the FastAPI server."""
    api_port = find_free_port(8000)
    print(f"Starting FastAPI server on port {api_port}...")
    
    env = os.environ.copy()
    env['API_PORT'] = str(api_port)
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        env=env,
        cwd=Path(__file__).parent
    )
    
    # Wait a bit for the server to start
    time.sleep(3)
    return process, api_port

def start_streamlit():
    """Start the Streamlit UI."""
    streamlit_port = find_free_port(8501)
    print(f"Starting Streamlit UI on port {streamlit_port}...")
    
    env = os.environ.copy()
    env['STREAMLIT_PORT'] = str(streamlit_port)
    
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui/streamlit_app.py", "--server.port", str(streamlit_port)],
        env=env,
        cwd=Path(__file__).parent
    )
    
    return process, streamlit_port

def main():
    """Main function to start both services."""
    processes = []
    
    try:
        # Start API server
        api_process, api_port = start_api_server()
        processes.append(api_process)
        
        # Update environment for Streamlit to use the correct API port
        os.environ['API_PORT'] = str(api_port)
        
        # Start Streamlit
        streamlit_process, streamlit_port = start_streamlit()
        processes.append(streamlit_process)
        
        print(f"\n🚀 Services started successfully!")
        print(f"📊 FastAPI Server: http://localhost:{api_port}")
        print(f"🎨 Streamlit UI: http://localhost:{streamlit_port}")
        print(f"\nPress Ctrl+C to stop all services...")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for process in processes:
            process.terminate()
        
        # Wait for processes to terminate
        for process in processes:
            process.wait()
        
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()
