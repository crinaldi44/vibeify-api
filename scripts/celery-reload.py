#!/usr/bin/env python3
"""Celery worker/beat with hot reload using watchfiles."""
import sys
import subprocess
import signal
from pathlib import Path

try:
    from watchfiles import watch
except ImportError:
    print("watchfiles not installed. Install it with: poetry add watchfiles")
    sys.exit(1)


def run_celery(args):
    """Run celery command."""
    cmd = ["celery"] + args
    process = subprocess.Popen(cmd)
    return process


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: celery-reload.py <celery-args>")
        print("Example: celery-reload.py -A vibeify_api.core.celery_app worker --loglevel=info")
        sys.exit(1)
    
    celery_args = sys.argv[1:]
    src_path = Path("/app/src")
    
    print(f"Starting Celery with hot reload: {' '.join(celery_args)}")
    print(f"Watching: {src_path}")
    
    process = None
    
    def restart_celery():
        """Restart celery process."""
        nonlocal process
        if process:
            print("\n[RELOAD]: File change detected, restarting Celery...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        
        process = run_celery(celery_args)
        print("[RELOAD]: Celery restarted")
    
    def signal_handler(sig, frame):
        """Handle shutdown signals."""
        if process:
            process.terminate()
            process.wait()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start initial process
    restart_celery()
    
    # Watch for file changes
    try:
        for changes in watch(src_path, recursive=True):
            if changes:
                restart_celery()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
