# ULTRAMAN.exe

**Self-Installing AI Engine in a Single File**

---

## Quick Start

1. Download `ULTRAMAN.exe`
2. Double-click to run
3. First run auto-installs, then starts chat

---

## What It Does

**First Run:**
- Creates `~/.ultraman/` directories
- Initializes SQLite memory database
- Sets up config.yaml
- Copies skills
- Registers global `ultraman` command
- Shows `ULTRAMAN READY!`

**Subsequent Runs:**
- Starts immediately with full AI system

---

## Building from Source

```bash
python build.py
```

Output: `dist/ULTRAMAN.exe`

---

## Command Line

```bash
ULTRAMAN.exe "help me build a website"
```

Pass arguments directly into chat system.

---

## Features

- Zero-config setup
- 180+ built-in tools
- Self-improving memory
- Behavior router
- MCP tools auto-loaded
- Skills auto-registered

---

## Files

```
~/.ultraman/
├── lifeline/        # Identity & personality
├── brain/          # Memory database
├── skills/         # Skill modules
├── sessions/       # Conversation history
├── checkpoints/   # State snapshots
└── config.yaml     # Configuration
```

---

**Built by the1frombeyond | H.A.I.L. MARY Project**