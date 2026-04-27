@echo off
setlocal EnableDelayedExpansion

:: ═══════════════════════════════════════════════════════════════
::
::    ╭────────────────────────────────────────────╮
::    │ █▀█ █▀█ █▀█ █▀█ █▀█ █▄ █ █ ▀█▀ █ █▀ │
::    │ █▀▀ █▀▄ █▄█ █▀▀ █▄█ █ ▀█ █  █  █ ▄█ │
::    │ ▀   ▀ ▀ ▀ ▀ ▀   ▀ ▀ ▀  ▀ ▀  ▀  ▀ ▀▀ │
::    ╰────────────────────────────────────────────╯
::
::    H.A.I.L. MARY - Helping AI Layer
::    The Self-Evolving AI Agent Engine
::    No venv needed - runs with system Python
::
:: ═══════════════════════════════════════════════════════════════

cls
echo.
echo  [bold #ff3e3e]╭────────────────────────────────────────────╮[bold #ff3e3e]
echo  [bold #ff3e3e]│[bold #00f2ff] █▀█ █▀█ █▀█ █▀█ █▀█ █▄ █ █ ▀█▀ █ █▀ [bold #00f2ff]│[bold #ff3e3e]│[bold #ff3e3e]
echo  [bold #ff3e3e]│[bold #00f2ff] █▀▀ █▀▄ █▄█ █▀▀ █▄█ █ ▀█ █  █  █ ▄█ [bold #00f2ff]│[bold #ff3e3e]│[bold #ff3e3e]
echo  [bold #ff3e3e]│[bold #00f2ff] ▀   ▀ ▀ ▀ ▀ ▀   ▀ ▀ ▀  ▀ ▀  ▀  ▀ ▀▀ [bold #00f2ff]│[bold #ff3e3e]│[bold #ff3e3e]
echo  [bold #ff3e3e]╰────────────────────────────────────────────╯[bold #ff3e3e]
echo.
echo  [bold]H.A.I.L. MARY - The Self-Evolving AI Agent Engine[bold]
echo  [dim]────────────────────────────────────────────────────[dim]
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [bold #f85149]✗[bold #f85149] Python not found! Please install Python 3.10+ from python.org
    echo.
    pause
    exit /b 1
)

echo  [bold #3fb950]✓[bold #3fb950] Python detected
echo.
echo  [cyan]▸ Installing dependencies...[/cyan]

:: Install Python dependencies (no venv needed)
pip install --quiet rich pyyaml requests pillow 2>nul
if %errorlevel% equ 0 (
    echo  [bold #3fb950]✓[bold #3fb950] Dependencies installed
) else (
    echo  [yellow]⚠ Some dependencies may need manual install[/yellow]
)

echo.
echo  [cyan]▸ Initializing ULTRAMAN core...[/cyan]

:: Initialize ~/.ultraman structure
python -c "import os, sys; sys.path.insert(0, '.'); from ultraman.core.config import ensure_ultraman_core; ensure_ultraman_core()" 2>nul
if %errorlevel% equ 0 (
    echo  [bold #3fb950]✓[bold #3fb950] Core initialized at ^~/.ultraman/^
) else (
    echo  [yellow]⚠ Core init failed - will retry on first run[/yellow]
)

echo.
echo  [cyan]▸ Checking Ollama...[/cyan]

:: Check for Ollama
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo  [yellow]⚠ Ollama not running[/yellow]
    echo  [dim]  Run 'ollama serve' or download from ollama.com[/dim]
) else (
    echo  [bold #3fb950]✓[bold #3fb950] Ollama connected
)

echo.
echo  [dim]────────────────────────────────────────────────────[dim]
echo.
echo  [bold #a371f7]╭────────────────────────────────────────────╮[bold #a371f7]
echo  [bold #a371f7]│[bold #3fb950]  SETUP COMPLETE - Launching ULTRAMAN...  [bold #3fb950]│[bold #a371f7]
echo  [bold #a371f7]╰────────────────────────────────────────────╯[bold #a371f7]
echo.
echo  [dim]Quick Commands:[/dim]
echo  [dim]  python main.py          - Start ULTRAMAN[/dim]
echo  [dim]  python superpowers.py   - Skill management[/dim]
echo  [dim]  python proponitis.py    - Training system[/dim]
echo.

:: Launch ULTRAMAN
python main.py

pause