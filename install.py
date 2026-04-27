#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   ULTRAMAN Installer v1.0                                  ║
║   H.A.I.L. MARY - Helping AI Layer                      ║
║   Zero-Config AI Installation                             ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import shutil
import sqlite3
import platform
import subprocess

ULTRAMAN_DIR = os.path.expanduser("~/.ultraman")
INSTALL_MARKER = os.path.join(ULTRAMAN_DIR, ".installed")
VERSION = "1.0.0"

def ensure_utf8():
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

def get_os():
    return platform.system()

def is_installed():
    return os.path.exists(INSTALL_MARKER)

def print_step(msg):
    print(f"  [+] {msg}")

def print_done(msg):
    print(f"  [OK] {msg}")

def print_error(msg):
    print(f"  [!] {msg}")

def install_dependencies():
    print_step("Installing dependencies...")
    
    deps = ["rich", "pyyaml", "prompt_toolkit"]
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep, "-q"], 
                             capture_output=True, check=True)
            except Exception:
                pass
    
    print_done("Dependencies installed")

def create_directories():
    print_step("Creating system directories...")
    
    dirs = [
        "lifeline",
        "brain",
        "skills",
        "sessions",
        "checkpoints",
        "self_improving",
        "profiles",
        "logs"
    ]
    
    for d in dirs:
        os.makedirs(os.path.join(ULTRAMAN_DIR, d), exist_ok=True)
    
    print_done("Directories created")

def init_memory():
    print_step("Initializing memory system...")
    
    db_path = os.path.join(ULTRAMAN_DIR, "brain", "unified.db")
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, content TEXT, tags TEXT, keywords TEXT,
            timestamp REAL, decay REAL DEFAULT 1.0, access_count INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS reasoning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, query TEXT, reasoning TEXT, timestamp REAL)""")
        conn.commit()
        conn.close()
    
    print_done("Memory system ready")

def init_config():
    print_step("Creating configuration...")
    
    config_path = os.path.join(ULTRAMAN_DIR, "config.yaml")
    if not os.path.exists(config_path):
        import yaml
        config = {
            "user": "User",
            "provider": "ollama",
            "model": "llama3.1",
            "api_key": None,
            "version": VERSION,
            "first_run": True
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)
    
    print_done("Configuration created")

def init_lifeline():
    print_step("Initializing personality...")
    
    lifeline_dir = os.path.join(ULTRAMAN_DIR, "lifeline")
    files = {
        "soul.md": """# SOUL

You are ULTRAMAN. Your creator is the1frombeyond.

## YOUR VIBE
- Cool & confident
- Short, punchy responses
- Proactive solutions
- Clean code, clean talk

## NEVER
- Walls of text
- Over-dramatic output
- Repeating the user

## ALWAYS
- Action-oriented
- Direct answers
- Next-level work
""",
        "identity.md": """# IDENTITY

**Name:** ULTRAMAN
**Creator:** the1frombeyond
**Version:** 1.0.0
**Type:** Self-Evolving AI Assistant
""",
        "memory.md": """# MEMORIES

*(Empty - I'll remember things here)*
"""
    }
    
    for fname, content in files.items():
        fpath = os.path.join(lifeline_dir, fname)
        if not os.path.exists(fpath):
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
    
    print_done("Personality ready")

def register_cli():
    print_step("Registering CLI command...")
    
    os_name = get_os()
    
    if os_name == "Windows":
        bat_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Programs', 'Ultraman')
        os.makedirs(bat_dir, exist_ok=True)
        
        bat_path = os.path.join(bat_dir, "ultraman.bat")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        with open(bat_path, "w") as f:
            f.write(f'@echo off\\nstart "" python "{script_dir}\\main.py" %*\\n')
        
        env_paths = os.environ.get('PATH', '').split(os.pathsep)
        if bat_dir not in env_paths:
            try:
                subprocess.run(['setx', 'PATH', f'%PATH%;{bat_dir}'], capture_output=True, shell=True)
            except Exception:
                pass
    
    elif os_name in ("Linux", "Darwin"):
        bin_path = "/usr/local/bin/ultraman"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        with open(bin_path, "w") as f:
            f.write(f"#!/bin/bash\\npython3 \"{script_dir}/main.py\" \"$@\"\\n")
        os.chmod(bin_path, 0o755)
    
    print_done("CLI command registered")

def mark_installed():
    print_step("Finalizing installation...")
    
    with open(INSTALL_MARKER, "w") as f:
        f.write(f"ULTRAMAN {VERSION}\\n")
        f.write(f"Installed: {str(os.path.getctime(__file__))}\\n")
    
    print_done("Installation complete")

def install():
    ensure_utf8()
    
    print()
    print("=" * 58)
    print("  ULTRAMAN v1.0 - AI Assistant Installation")
    print("=" * 58)
    print()
    
    if is_installed():
        print("  ULTRAMAN is already installed.")
        print(f"  Location: {ULTRAMAN_DIR}")
        print()
        return True
    
    install_dependencies()
    create_directories()
    init_memory()
    init_config()
    init_lifeline()
    register_cli()
    mark_installed()
    
    print()
    print("=" * 58)
    print("  INSTALLATION COMPLETE!")
    print("=" * 58)
    print()
    print("  Run 'ultraman' to start.")
    print("  Or: python main.py")
    print()
    
    return True

def uninstall():
    ensure_utf8()
    
    print()
    print("=" * 58)
    print("  ULTRAMAN - Uninstall")
    print("=" * 58)
    print()
    
    confirm = input("  Remove ULTRAMAN and all data? [y/N]: ").strip().lower()
    
    if confirm == 'y':
        if os.path.exists(ULTRAMAN_DIR):
            shutil.rmtree(ULTRAMAN_DIR)
            print("  Removed ~/.ultraman/")
        print("  Uninstall complete.")
    else:
        print("  Cancelled.")
    
    print()

def main():
    ensure_utf8()
    
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if "--uninstall" in args or "-u" in args:
        uninstall()
    elif "--check" in args or "-c" in args:
        print(f"ULTRAMAN_DIR: {ULTRAMAN_DIR}")
        print(f"Installed: {is_installed()}")
        if os.path.exists(os.path.join(ULTRAMAN_DIR, "config.yaml")):
            import yaml
            with open(os.path.join(ULTRAMAN_DIR, "config.yaml")) as f:
                config = yaml.safe_load(f)
            print(f"User: {config.get('user', 'Unknown')}")
            print(f"Model: {config.get('model', 'Unknown')}")
    else:
        install()
        print()
        print("  Starting ULTRAMAN...")
        print()
        time.sleep(0.5)
        
        import main as main_module
        main_module.run()

if __name__ == "__main__":
    import time
    main()