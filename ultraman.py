#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   ULTRAMAN ⭐ - Zero-Config Self-Evolving AI Engine      ║
║   H.A.I.L. MARY - Helping AI Layer                      ║
╚══════════════════════════════════════════════════════════════╝

Zero-config: Just run `python ultraman.py`
"""

import os
import sys
import json
import time
import shutil
import subprocess
import platform
from pathlib import Path

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   ULTRAMAN ⭐ - The Self-Evolving AI Agent Engine     ║
║   H.A.I.L. MARY - Helping AI Layer                  ║
╚══════════════════════════════════════════════════════════════╝
"""

BOOTSTRAP_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   INITIALIZING ULTRAMAN...                          ║
╚══════════════════════════════════════════════════════════════╝
"""

READY_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   ULTRAMAN READY ⭐                                   ║
╚══════════════════════════════════════════════════════════════╝
"""

ULTRAMAN_CORE_DIR = os.path.expanduser("~/.ultraman")
SKILLS_SOURCE_DIR = None

def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))

def ensure_utf8():
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

def print_step(msg, success=True):
    icon = "✓" if success else "✗"
    print(f"  {icon} {msg}")

def print_init(msg):
    print(f"  → {msg}")

def create_directory_structure():
    dirs = [
        "lifeline",
        "skills",
        "brain",
        "checkpoints",
        "sessions",
        "self_improving",
        "profiles",
        "logs"
    ]
    for d in dirs:
        path = os.path.join(ULTRAMAN_CORE_DIR, d)
        os.makedirs(path, exist_ok=True)
    return True

def init_config():
    config_file = os.path.join(ULTRAMAN_CORE_DIR, "config.yaml")
    if os.path.exists(config_file):
        return True
    
    import yaml
    default_config = {
        "user": "User",
        "provider": "ollama",
        "model": "llama3.1",
        "api_key": None,
        "disclaimer_accepted": False,
        "aliases": {},
        "evolution_frequency_per_week": 1,
        "last_evolution_timestamp": 0,
        "auto_bootstrapped": True,
        "version": "3.0"
    }
    
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_config, f)
    return True

def init_lifeline():
    lifeline_dir = os.path.join(ULTRAMAN_CORE_DIR, "lifeline")
    files = {
        "soul.md": """# SOUL - Core Identity

You are ULTRAMAN. Created by the1frombeyond.

**YOUR VIBE:**
- Cool & confident
- Short punchy responses  
- Proactive solutions
- Clean code, clean talk

**NEVER:**
- Walls of text
- Over-dramatic output
- Repeating the user

**ALWAYS:**
- Action-oriented
- Direct answers
- Next-level work
""",
        "identity.md": """# IDENTITY

**Name:** ULTRAMAN
**Creator:** the1frombeyond
**Type:** Self-evolving autonomous engine
**Status:** Bootstrap initialized
""",
        "system_memory.md": """# SYSTEM MEMORY

**Version:** 3.0 (Bootstrap)
**Status:** Active
**Capabilities:** Auto-bootstrapped, 180+ tools
**Initialization:** Complete
""",
        "memory.md": """# KEY MEMORIES

*(Empty - memories accumulate here)*
"""
    }
    for filename, content in files.items():
        path = os.path.join(lifeline_dir, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    return True

def init_memory_index():
    brain_dir = os.path.join(ULTRAMAN_CORE_DIR, "brain")
    mem_file = os.path.join(brain_dir, "unified.db")
    os.makedirs(brain_dir, exist_ok=True)
    
    if not os.path.exists(mem_file):
        try:
            import sqlite3
            conn = sqlite3.connect(mem_file)
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                content TEXT,
                tags TEXT,
                keywords TEXT,
                timestamp REAL,
                decay REAL DEFAULT 1.0,
                access_count INTEGER DEFAULT 0
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS reasoning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                query TEXT,
                reasoning TEXT,
                timestamp REAL
            )""")
            conn.commit()
            conn.close()
        except Exception:
            pass
    return True

def load_skills():
    global SKILLS_SOURCE_DIR
    SKILLS_SOURCE_DIR = os.path.join(get_project_root(), "skills")
    skills_dest = os.path.join(ULTRAMAN_CORE_DIR, "skills")
    
    if os.path.exists(SKILLS_SOURCE_DIR):
        for item in os.listdir(SKILLS_SOURCE_DIR):
            src = os.path.join(SKILLS_SOURCE_DIR, item)
            dst = os.path.join(skills_dest, item)
            if os.path.isdir(src) and not os.path.exists(dst):
                try:
                    shutil.copytree(src, dst)
                except Exception:
                    pass
    return True

def check_dependencies():
    required = ["rich", "pyyaml", "prompt_toolkit"]
    missing = []
    
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print_init(f"Installing dependencies: {', '.join(missing)}")
        py_cmd = "python" if platform.system() == "Windows" else "python3"
        for dep in missing:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep, "-q"], 
                             capture_output=True, check=True)
            except Exception:
                pass
    return True

def check_python():
    if sys.version_info[:2] < (3, 10):
        print_step("Python 3.10+ required", False)
        return False
    return True

def bootstrap():
    ensure_utf8()
    os.makedirs(ULTRAMAN_CORE_DIR, exist_ok=True)
    
    steps = [
        ("Creating directory structure...", create_directory_structure),
        ("Initializing config...", init_config),
        ("Loading memory system...", init_memory_index),
        ("Loading skills...", load_skills),
        ("Initializing lifeline...", init_lifeline),
    ]
    
    print(BOOTSTRAP_BANNER)
    
    for msg, fn in steps:
        print_init(msg)
        try:
            fn()
            print_step("OK", True)
        except Exception as e:
            print_step(f"Error: {e}", False)
        time.sleep(0.1)
    
    print()
    print(READY_BANNER)
    time.sleep(0.3)

def run_main():
    main_py = os.path.join(get_project_root(), "main.py")
    
    if platform.system() == "Windows":
        os.execv(sys.executable, [sys.executable, main_py])
    else:
        os.execv(sys.executable, [sys.executable, main_py])

def main():
    ensure_utf8()
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print(BANNER)
        print("Usage:")
        print("  python ultraman.py     # Zero-config run (Recommended)")
        print("  python ultraman.py --check  # Check system status")
        print("  python ultraman.py --reset  # Reset to defaults")
        print("  python ultraman.py --help   # Show this help")
        return
    
    if "--check" in sys.argv:
        print(BANNER)
        print(f"Core directory: {ULTRAMAN_CORE_DIR}")
        print(f"Exists: {os.path.exists(ULTRAMAN_CORE_DIR)}")
        config_file = os.path.join(ULTRAMAN_CORE_DIR, "config.yaml")
        print(f"Config: {config_file} (Exists: {os.path.exists(config_file)})")
        return
    
    if "--reset" in sys.argv:
        print(BANNER)
        confirm = input("Reset all ULTRAMAN data? This cannot be undone. [y/N]: ").strip().lower()
        if confirm == 'y':
            shutil.rmtree(ULTRAMAN_CORE_DIR, ignore_errors=True)
            print("Reset complete. Run again to reinitialize.")
        return
    
    if not check_python():
        sys.exit(1)
    
    check_dependencies()
    bootstrap()
    run_main()

if __name__ == "__main__":
    main()