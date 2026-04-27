#!/bin/bash

# ═══════════════════════════════════════════════════════════════
#
#    ╭────────────────────────────────────────────╮
#    │ █▀█ █▀█ █▀█ █▀█ █▀█ █▄ █ █ ▀█▀ █ █▀ │
#    │ █▀▀ █▀▄ █▄█ █▀▀ █▄█ █ ▀█ █  █  █ ▄█ │
#    │ ▀   ▀ ▀ ▀ ▀ ▀   ▀ ▀ ▀  ▀ ▀  ▀  ▀ ▀▀ │
#    ╰────────────────────────────────────────────╯
#
#    H.A.I.L. MARY - Helping AI Layer
#    The Self-Evolving AI Agent Engine
#    No venv needed - runs with system Python
#
# ═══════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

echo ""
echo -e "${BOLD}${CYAN}╭────────────────────────────────────────────╮${RESET}"
echo -e "${BOLD}${CYAN}│[bold #ff3e3e] █▀█ █▀█ █▀█ █▀█ █▀█ █▄ █ █ ▀█▀ █ █▀ [bold #ff3e3e]│${RESET}"
echo -e "${BOLD}${CYAN}│[bold #ff3e3e] █▀▀ █▀▄ █▄█ █▀▀ █▄█ █ ▀█ █  █  █ ▄█ [bold #ff3e3e]│${RESET}"
echo -e "${BOLD}${CYAN}│[bold #ff3e3e] ▀   ▀ ▀ ▀ ▀ ▀   ▀ ▀ ▀  ▀ ▀  ▀  ▀ ▀▀ [bold #ff3e3e]│${RESET}"
echo -e "${BOLD}${CYAN}╰────────────────────────────────────────────╯${RESET}"
echo ""
echo -e "${BOLD}H.A.I.L. MARY - The Self-Evolving AI Agent Engine${RESET}"
echo -e "${YELLOW}────────────────────────────────────────────────────${RESET}"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python not found!${RESET}"
    echo "   Please install Python 3.10+ from python.org"
    exit 1
fi

PYTHON_CMD="python3"
PY_VERSION=$($PYTHON_CMD --version | grep -oP '\d+\.\d+' | head -1)
echo -e "${GREEN}✓${RESET} Python $PY_VERSION detected"

# Check version
if [ "$(echo "$PY_VERSION < 3.10" | bc -l)" = "1" ]; then
    echo -e "${RED}✗ Python 3.10+ required${RESET}"
    exit 1
fi

echo ""
echo -e "${CYAN}▸ Installing dependencies...${RESET}"

# Install Python dependencies (no venv needed)
for dep in rich pyyaml requests pillow; do
    if $PYTHON_CMD -c "import $dep" &> /dev/null; then
        echo -e "  ${GREEN}✓${RESET} $dep already installed"
    else
        $PYTHON_CMD -m pip install $dep -q 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓${RESET} Installed $dep"
        else
            echo -e "  ${YELLOW}⚠${RESET} Failed to install $dep"
        fi
    fi
done

echo ""
echo -e "${CYAN}▸ Initializing ULTRAMAN core...${RESET}"

# Initialize ~/.ultraman structure
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
$PYTHON_CMD -c "
import os, sys
sys.path.insert(0, r'$SCRIPT_DIR')
from ultraman.core.config import ensure_ultraman_core
ensure_ultraman_core()
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓${RESET} Core initialized at ~/.ultraman/"
else
    echo -e "  ${YELLOW}⚠${RESET} Core init failed - will retry on first run"
fi

echo ""
echo -e "${CYAN}▸ Checking Ollama...${RESET}"

# Check for Ollama
if curl -s http://127.0.0.1:11434/api/tags &> /dev/null; then
    echo -e "  ${GREEN}✓${RESET} Ollama connected"
else
    echo -e "  ${YELLOW}⚠${RESET} Ollama not running"
    echo "    Run 'ollama serve' or download from ollama.com"
fi

echo ""
echo -e "${YELLOW}────────────────────────────────────────────────────${RESET}"
echo ""
echo -e "${BOLD}${GREEN}╭────────────────────────────────────────────╮${RESET}"
echo -e "${BOLD}${GREEN}│  SETUP COMPLETE - Launching ULTRAMAN...  │${RESET}"
echo -e "${BOLD}${GREEN}╰────────────────────────────────────────────╯${RESET}"
echo ""
echo -e "${CYAN}Quick Commands:${RESET}"
echo "  python main.py          - Start ULTRAMAN"
echo "  python superpowers.py   - Skill management"
echo "  python proponitis.py    - Training system"
echo ""

# Launch ULTRAMAN
cd "$SCRIPT_DIR"
exec $PYTHON_CMD main.py