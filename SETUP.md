# ULTRAMAN Setup Guide

## Quick Start (One Command)

```bash
# Clone & run (no venv needed)
git clone https://github.com/the1frombeyond/HAIL.MARY.git
cd HAIL.MARY
python install.py
python main.py
```

## Prerequisites

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Ollama** (for local AI)
   ```bash
   # Install Ollama
   winget install Ollama.Ollama
   
   # Or download from https://ollama.com
   
   # Install model
   ollama pull ministral-3:latest
   ```

## Installation Methods

### Method 1: Automatic (Recommended)
```bash
python install.py
```

### Method 2: Manual
```bash
pip install rich pyyaml requests pillow
python main.py
```

### Method 3: Portable (No Install)
```bash
# Just run directly
python main.py
```

## First Run Setup

On first run, ULTRAMAN will:
1. Create `~/.ultraman/` directory structure
2. Copy skills to `~/.ultraman/skills/`
3. Create lifeline files in `~/.ultraman/lifeline/`
4. Initialize memory database

## Portability

All core data is stored in `~/.ultraman/`:
- Copy the folder to a new machine
- Run `python main.py` again
- Everything syncs automatically

## Troubleshooting

**Ollama not responding?**
```bash
ollama serve
```

**Port conflict?**
```bash
# Kill existing Ollama process
taskkill /f /im ollama.exe
# Then restart
ollama serve
```

## Quick Commands

```bash
# Main CLI
python main.py

# Superpowers CLI (skill management)
python superpowers.py

# Proponitis CLI (training)
python proponitis.py

# Quick setup
python install.py
```