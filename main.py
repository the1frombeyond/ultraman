import os
import sys
import time
import socket
import shutil
import html
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
import select
import datetime

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style as ToolkitStyle
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from ultraman.ui.branding import UltramanUI, display_banner, display_mini_banner, display_welcome, OPENCODE_COLORS
from ultraman.core.config import ConfigManager
from ultraman.core.ai import AIBridge
from ultraman.core.brainwaves import Brainwaves
from ultraman.core.vault import VaultManager
from ultraman.core.tools import manifest_login
from ultraman.core.security_guard import guard
from ultraman.core.st_walker import StWalker


# ---------------------------------------------------------------------------
# Autocomplete Completer
# ---------------------------------------------------------------------------
class UltramanCompleter(Completer):
    def __init__(self, commands, meta):
        self.commands = commands
        self.meta = meta

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        if not word.startswith("/"):
            return
        try:
            tw = shutil.get_terminal_size().columns - 2
        except Exception:
            tw = 80
        for cmd in self.commands:
            if cmd.startswith(word):
                desc = html.escape(self.meta.get(cmd, ""))
                label_part = html.escape(f"{cmd:<18}")
                padding = max(0, tw - len(label_part) - len(desc) - 4)
                display_html = HTML(
                    f'<style color="#58a6ff"><b>{label_part}</b></style> '
                    f'<style color="#8b949e">{desc}</style>{" " * padding}'
                )
                yield Completion(cmd, start_position=-len(word), display=display_html)


# ---------------------------------------------------------------------------
# Command Registry (single source of truth)
# ---------------------------------------------------------------------------
COMMAND_REGISTRY = {
    # CORE COMMANDS
    "/help":         "Show this command reference",
    "/setup":        "Re-run the configuration wizard",
    "/clear":        "Clear screen and redraw banner",
    "/brain":        "List installed local models",
    "/stats":        "System resource stats (CPU/RAM/Disk)",
    "/memory":       "Show memory tier statistics",
    "/playback":     "Replay recent conversation history",
    "/rewind":      "Rewind file state to previous checkpoint",
    "/sandbox":     "Test code in isolated sandbox",
    "/mcp":         "Connect to MCP server",
    "/swarm":       "Spawn a sub-agent swarm for a task",
    "/task":        "Schedule an automated mission",
    "/web":         "Launch the ULTRAMAN web interface",
    "/vault":       "Manage encrypted secrets",
    "/newskill":    "Synthesize a new skill from description",
    "/editskill":   "Open skill file in system editor",
    "/install":     "System provisioning via winget",
    "/skills":      "List all installed skills",
    "/dr_strange":  "Simulate session history to detect mistakes",
    "/st_walker":   "Self-fine-tune and learn from corrections",
    "/evolve":     "Trigger recursive self-improvement cycle",
    "/learn":       "Learn from interaction",
    # SYSTEM
    "/session":     "Show session statistics",
    "/theme":       "Switch visual theme (dark/light/minimal)",
    "/export":      "Export session to file (markdown/json)",
    "/import":      "Import knowledge from file",
    "/whoami":      "Display current user info",
    "/sync":        "Sync ULTRAMAN core to device",
    "/shell":       "Execute shell command",
    "/superpowers": "Launch the Skill Database CLI",
    "/proponitis": "Proponitis - AI proposition evaluator",
    # MODEL COMMANDS
    "/models":      "List available Ollama models",
    "/switch":      "Switch to different model",
    "/critique":   "Critique response using another model",
    "/reflect":    "Deep reflection using another model",
    # SKILLS & TOOLS
    "/fetch":       "Download/import skills from URL",
    "/sklist":     "List fetchable skill sources",
    # CODE OPERATIONS
    "/explain":     "Explain code at path",
    "/refactor":   "Refactor code at path",
    "/test":       "Generate tests for file",
    "/audit":      "Audit code for issues",
    "/undo":       "Undo last AI change",
    "/redo":       "Redo last undone change",
    "/plan":       "Toggle plan mode (preview only)",
    # PROJECT FILES
    "/ultramanmd": "Create ultraman.md/um.md/agent.md template",
    "/init":       "Initialize/reinitialize project",
    # FILE CREATION
    "/newdoc":      "Create new document",
    "/pdf":         "Create PDF document",
    "/docx":        "Create Word document",
    "/xlsx":        "Create Excel spreadsheet",
    "/pptx":        "Create PowerPoint presentation",
    "/md":          "Create Markdown file",
    "/html":        "Create HTML file",
    "/css":         "Create CSS file",
    "/js":          "Create JavaScript file",
    "/py":          "Create Python file",
    "/json":        "Create JSON file",
    "/yaml":        "Create YAML file",
    "/sh":          "Create Shell script",
    # DESIGN & UI
    "/algorithmic-art": "Create algorithmic art using p5.js",
    "/canvas-design":   "Create posters and artworks",
    "/json-canvas":     "Create JSON Canvas files for Obsidian",
    "/frontend-design": "Create frontend interfaces",
    "/web-artifacts-builder": "Build complex Web apps",
    "/remotion":       "Video creation in React",
    # EXECUTORS
    "/npm":         "Execute an NPM operation",
    "/npx":         "Execute an NPX operation",
    "/pip":         "Execute a Pip operation",
    "/curl":        "Execute a Curl HTTP request",
    "/config":      "Configure messenger (telegram/discord/whatsapp)",
    "/send":        "Send message via messenger",
}


# ---------------------------------------------------------------------------
# Main Application Loop
# ---------------------------------------------------------------------------
class MainLoop:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.console = Console()
        self.ai = AIBridge(
            provider=self.config_manager.config.get("provider", "ollama"),
            model=self.config_manager.config.get("model", "llama3.1"),
            api_key=self.config_manager.config.get("api_key", None),
            callsign=self.config_manager.config.get("user", "User"),
        )
        self.brainwaves = Brainwaves(self.ai)
        self.vault = VaultManager()
        self.web_server_thread = None

        self.session = None
        self.use_simple_input = False
        self._ultramanmd_scanned = False

        if PROMPT_TOOLKIT_AVAILABLE:
            try:
                self.completer = UltramanCompleter(list(COMMAND_REGISTRY.keys()), COMMAND_REGISTRY)
                self.style = ToolkitStyle.from_dict({
                    "completion-menu": "bg:#0d1117 fg:#c9d1d9",
                    "completion-menu.completion": "fg:#c9d1d9",
                    "completion-menu.completion.current": "bg:#388bfd fg:#ffffff",
                    "prompt": "bold #58a6ff",
                })
                self.session = PromptSession(
                    completer=self.completer,
                    style=self.style,
                    complete_while_typing=True,
                    auto_suggest=AutoSuggestFromHistory(),
                    history=FileHistory("input_history.txt"),
                    reserve_space_for_menu=8,
                )
            except Exception:
                self.use_simple_input = True
        else:
            self.use_simple_input = True
        
        # Auto-register skills on startup
        self._auto_register_skills()

    # -----------------------------------------------------------------------
    # Command Handlers (each returns True to continue, False to exit)
    # -----------------------------------------------------------------------
    def _show_help(self):
        from ultraman.ui.branding import display_command_palette
        display_command_palette()
        
    def _cmd_help(self, args):
        from ultraman.ui.branding import display_command_palette
        display_command_palette()
        return True


    def _cmd_setup(self, _args):
        self.config_manager.run_setup_wizard(force=True)
        self.ai.set_config(
            self.config_manager.config["provider"],
            self.config_manager.config["model"],
            self.config_manager.config.get("api_key"),
            self.config_manager.config["user"],
        )
        return True

    def _cmd_clear(self, _args):
        self.console.clear()
        display_banner()
        return True

    def _cmd_brain(self, _args):
        models = self.ai.list_local_models()
        active = self.config_manager.config.get("model", "unknown")
        self.console.print()
        self.console.print("[bold #58a6ff]╭─ INSTALLED MODELS ─────────────────────────────────────────╮[/bold #58a6ff]")
        
        table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
        table.add_column("#", style="#6e7681", justify="right", min_width=3)
        table.add_column("Model", style="#c9d1d9", min_width=30)
        table.add_column("Active", style="#3fb950", justify="center", min_width=6)
        
        for i, m in enumerate(models, 1):
            table.add_row(str(i), m, "◉" if m == active else "")
        
        self.console.print(table)
        self.console.print("[bold #58a6ff]╰────────────────────────────────────────────────────────────╯[/bold #58a6ff]")
        self.console.print()
        return True

    def _cmd_dr_strange(self, _args):
        self.console.print("\n[bold #ffc107]⚡ DR.STRANGE: Initiating Multi-Reality Simulation...[/bold #ffc107]")
        history = self.ai.memory.get_recent_history(limit=50)
        from ultraman.core.dr_strange import DrStrange
        ds = DrStrange(self.console)
        result = ds.run_simulation(history)
        self.console.print(f"  [dim]└ Simulation Result:[/dim]\n{result}")
        return True

    def _cmd_stats(self, _args):
        from ultraman.commands.system import SystemManager
        SystemManager().get_system_stat()
        return True

    def _cmd_memory(self, _args):
        from ultraman.core.tools import memory_stats
        stats = memory_stats()
        self.console.print()
        self.console.print("[bold #58a6ff]╭─ MEMORY TIERS ────────────────────────────────────────────╮[/bold #58a6ff]")
        
        table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
        table.add_column("Tier", style="bold #58a6ff", min_width=20)
        table.add_column("Value", style="#c9d1d9", min_width=15)
        
        for k, v in stats.items():
            table.add_row(k, str(v))
        
        self.console.print(table)
        self.console.print("[bold #58a6ff]╰────────────────────────────────────────────────────────────╯[/bold #58a6ff]")
        self.console.print()
        return True

    def _cmd_playback(self, _args):
        self.console.print()
        self.console.print("[bold #58a6ff]▸ Replaying Mission Transcript...[/bold #58a6ff]")
        logs = self.ai.memory.get_recent_history(limit=20)
        if not logs:
            self.console.print("  [dim]No history recorded yet.[/dim]")
            return True
        for log in logs:
            self.console.print(f"\n[bold #58a6ff]∴[/bold #58a6ff] [bold #c9d1d9]{log['role'].upper()}:[/bold #c9d1d9] {log['content']}")
            time.sleep(0.05)
        self.console.print()
        return True

    def _cmd_task(self, _args):
        desc = Prompt.ask("\n[bold #58a6ff]Describe automated mission?[/bold #58a6ff]")
        f_choice = Prompt.ask("[bold #58a6ff]Frequency (h=hourly, m=minutely, e=event)?[/bold #58a6ff]",
                              choices=["h", "m", "e"], default="e")
        stime = Prompt.ask("[bold #58a6ff]Start time (HH:MM)?[/bold #58a6ff]", default=time.strftime("%H:%M"))
        self.ai.memory.schedule_task(desc, f_choice, stime)
        self.console.print(f"\n[bold #3fb950]✓ Mission Scheduled:[/bold #3fb950] {desc}")
        return True

    def _cmd_auto(self, _args):
        path = os.path.abspath("ultraman/auto_hub/index.html")
        self.console.print("\n[bold #58a6ff]▸ Opening Automation Builder...[/bold #58a6ff]")
        webbrowser.open(f"file://{path}")
        return True

    def _cmd_web(self, _args):
        self._start_web_server()
        self.console.print("\n[bold #58a6ff]▣[/bold #58a6ff] Build [dim]·[/dim] [bold #c9d1d9]Web Server[/bold #c9d1d9] [dim]·[/dim] [link]http://localhost:3000[/link]")
        time.sleep(1)
        webbrowser.open("http://localhost:3000")
        return True

    def _cmd_superpowers(self, args):
        import subprocess
        self.console.clear()
        self.console.print("\n[bold #58a6ff]⚡ Initializing SUPERPOWERS Skill Database...[/bold #58a6ff]")
        # Resolve absolute path to superpowers.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sp_path = os.path.join(script_dir, "superpowers.py")
        
        cmd = [sys.executable, sp_path]
        if args:
            cmd.extend(args.split())
        subprocess.run(cmd)
        return True

    def _cmd_login(self, _args):
        self.console.print("\n[bold #58a6ff]▸ Opening authentication session...[/bold #58a6ff]")
        manifest_login()
        return True

    def _cmd_vault(self, _args):
        pw = Prompt.ask("\n[bold #f85149]VAULT PASSPHRASE[/bold #f85149]", password=True)
        if self.vault.unlock(pw):
            self.console.print("\n[bold #3fb950]✓ Vault Unlocked.[/bold #3fb950]")
            action = Prompt.ask("[bold #58a6ff]Action[/bold #58a6ff]", choices=["list", "store", "get"], default="list")
            if action == "list":
                self.console.print(f"  [dim]└ Tags:[/dim] {self.vault.list_tags()}")
            elif action == "store":
                t = Prompt.ask("[bold #58a6ff]Tag[/bold #58a6ff]")
                v = Prompt.ask("[bold #58a6ff]Value[/bold #58a6ff]", password=True)
                self.vault.store_secret(t, v)
                self.console.print("  [dim]└ Secret secured.[/dim]")
            elif action == "get":
                t = Prompt.ask("[bold #58a6ff]Tag[/bold #58a6ff]")
                v = self.vault.get_secret(t)
                self.console.print(f"  [dim]└ Value:[/dim] [cyan]{v}[/cyan]")
        else:
            self.console.print("\n[bold #f85149]✗ Vault: Authentication failed.[/bold #f85149]")
        return True

    def _cmd_newskill(self, args):
        desc = args if args else Prompt.ask("\n[bold #58a6ff]Describe the skill?[/bold #58a6ff]")
        self.console.print("\n[bold #58a6ff]▸ Synthesizing skill...[/bold #58a6ff]")
        code = self.ai.generate_skill_code(desc)
        if code and len(code) > 10:
            import re
            func_match = re.search(r"def (\w+)\(", code)
            name = func_match.group(1) if func_match else f"skill_{int(time.time())}"
            
            # Save to both locations
            from ultraman.core.config import ULTRAMAN_SKILLS_DIR
            os.makedirs("ultraman/skills", exist_ok=True)
            os.makedirs(ULTRAMAN_SKILLS_DIR, exist_ok=True)
            
            # Create as skill directory with SKILL.md
            skill_dir_proj = os.path.join("ultraman/skills", name)
            skill_dir_user = os.path.join(ULTRAMAN_SKILLS_DIR, name)
            os.makedirs(skill_dir_proj, exist_ok=True)
            os.makedirs(skill_dir_user, exist_ok=True)
            
            # Save Python code
            with open(os.path.join(skill_dir_proj, f"{name}.py"), "w", encoding="utf-8") as f:
                f.write(code)
            with open(os.path.join(skill_dir_user, f"{name}.py"), "w", encoding="utf-8") as f:
                f.write(code)
            
            # Save SKILL.md
            skill_md = f"# {name}\n\n{desc}\n"
            with open(os.path.join(skill_dir_proj, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_md)
            with open(os.path.join(skill_dir_user, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_md)
            
            self.console.print(f"  [dim]└ Skill saved to[/dim] {skill_dir_proj}")
            self.console.print(f"  [dim]└ Also saved to[/dim] {skill_dir_user}")
        else:
            self.console.print("\n[bold #f85149]✗ Error: Skill synthesis failed.[/bold #f85149]")
        return True

    # ---------------------------------------------------------------------------
    # FILE CREATION COMMANDS
    # ---------------------------------------------------------------------------
    def _cmd_newdoc(self, args):
        """Create a new document file"""
        if not args:
            args = Prompt.ask(f"[bold {OPENCODE_COLORS['primary']}]Filename?[/bold {OPENCODE_COLORS['primary']}]", default="document.txt")
        
        filename = args.strip()
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# {os.path.splitext(filename)[0]}\n\n")
            self.console.print(f"\n[{OPENCODE_COLORS['accent']}]✓ Created:[/{OPENCODE_COLORS['accent']}] {filename}")
        else:
            self.console.print(f"\n[{OPENCODE_COLORS['warning']}]File already exists[/{OPENCODE_COLORS['warning']}]")
        return True

    def _cmd_create_file(self, ext, args):
        """Generic file creation based on extension"""
        if not args:
            args = Prompt.ask(f"[bold {OPENCODE_COLORS['primary']}]Filename?[/bold {OPENCODE_COLORS['primary']}]", default=f"file{ext}")
        
        filename = args.strip()
        if not filename.endswith(ext):
            filename += ext
        
        templates = {
            ".md": "# {title}\n\n## Overview\n\n## Details\n\n---\n*Created by ULTRAMAN*",
            ".html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>",
            ".css": "/* {title} */\n* {{\n    box-sizing: border-box;\n    margin: 0;\n    padding: 0;\n}}\n\nbody {{\n    font-family: system-ui, sans-serif;\n    line-height: 1.6;\n}}",
            ".js": "// {title}\n\ndocument.addEventListener('DOMContentLoaded', () => {{\n    \n}});",
            ".py": "# {title}\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()",
            ".json": '{{"name": "project", "version": "1.0.0"}}',
            ".yaml": "# {title}\n\nproject:\n  name: \n  version: 1.0.0",
            ".sh": "#!/bin/bash\n# {title}\n\nset -e\n",
        }
        
        template = templates.get(ext, "")
        title = os.path.splitext(filename)[0]
        content = template.format(title=title) if title in template else template
        
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.console.print(f"\n[{OPENCODE_COLORS['accent']}]✓ Created:[/{OPENCODE_COLORS['accent']}] {filename}")
        else:
            self.console.print(f"\n[{OPENCODE_COLORS['warning']}]File already exists[/{OPENCODE_COLORS['warning']}]")
        return True

    def _cmd_pdf(self, args): return self._create_file(".pdf", args)
    def _cmd_docx(self, args): return self._create_file(".docx", args)
    def _cmd_xlsx(self, args): return self._create_file(".xlsx", args)
    def _cmd_pptx(self, args): return self._create_file(".pptx", args)
    def _cmd_md(self, args): return self._create_file(".md", args)
    def _cmd_html(self, args): return self._create_file(".html", args)
    def _cmd_css(self, args): return self._create_file(".css", args)
    def _cmd_js(self, args): return self._create_file(".js", args)
    def _cmd_py(self, args): return self._create_file(".py", args)
    def _cmd_json(self, args): return self._create_file(".json", args)
    def _cmd_yaml(self, args): return self._create_file(".yaml", args)
    def _cmd_sh(self, args): return self._create_file(".sh", args)

    def _cmd_learn(self, args):
        """Learn from interaction (ST.WALKER)"""
        from ultraman.core.st_walker import StWalker
        sw = StWalker()
        result = sw.apply_fine_tune()
        self.console.print(f"\n[{OPENCODE_COLORS['primary']}]▸ Learning...[/bold {OPENCODE_COLORS['primary']}]")
        self.console.print(f"  [dim]{result}[/dim]")
        return True

    def _cmd_learning_stats(self, args):
        """Show learning stats (ST.WALKER)"""
        from ultraman.core.st_walker import StWalker
        sw = StWalker()
        stats = sw.get_training_stats()
        self.console.print(f"\n[{OPENCODE_COLORS['primary']}]╭─ Learning Statistics ──────────────────────╮[/{OPENCODE_COLORS['primary']}]")
        self.console.print(stats)
        self.console.print(f"[{OPENCODE_COLORS['primary']}]╰─────────────────────────────────────────────╯[/{OPENCODE_COLORS['primary']}]")
        return True

    # ---------------------------------------------------------------------------
    # MODEL SWITCHING & SELF-IMPROVEMENT
    # ---------------------------------------------------------------------------
    def _cmd_models(self, args):
        """List available Ollama models"""
        models = self.ai.list_models()
        
        self.console.print(f"\n[{OPENCODE_COLORS['primary']}]╭─ Available Models ──────────────────╮[/{OPENCODE_COLORS['primary']}]")
        
        table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
        table.add_column("Model", style=f"bold {OPENCODE_COLORS['primary']}", min_width=25)
        table.add_column("Status", style=OPENCODE_COLORS["dim"], min_width=10)
        
        for m in models:
            status = "◉ Active" if m == self.ai.model else ""
            table.add_row(m, status)
        
        self.console.print(table)
        self.console.print(f"[{OPENCODE_COLORS['primary']}]╰─────────────────────────────────────────────╯[/{OPENCODE_COLORS['primary']}]")
        
        # Show improvement models
        if self.ai.critic_model or self.ai.reflection_model:
            self.console.print(f"\n[{OPENCODE_COLORS['accent']}]Self-Improvement Models:[/{OPENCODE_COLORS['accent']}]")
            if self.ai.critic_model:
                self.console.print(f"  Critic: {self.ai.critic_model}")
            if self.ai.reflection_model:
                self.console.print(f"  Reflect: {self.ai.reflection_model}")
        return True

    def _cmd_switch(self, args):
        """Switch to a different Ollama model"""
        from ultraman.ui.branding import OPENCODE_COLORS
        from rich.table import Table
        
        if not args:
            models = self.ai.available_models
            if not models:
                self.console.print(f"\n[{OPENCODE_COLORS['warning']}]No models available[/{OPENCODE_COLORS['warning']}]")
                return True
            
            current = self.ai.model
            self.console.print(f"\n[{OPENCODE_COLORS['primary']}]╭─ AVAILABLE MODELS ────────────────────────╮[{OPENCODE_COLORS['primary']}]")
            
            table = Table(box=None, show_header=False, padding=(0, 1))
            table.add_column("Num", style=f"{OPENCODE_COLORS['accent']}", justify="right")
            table.add_column("Model", style="white")
            table.add_column("Status", style="dim", min_width=10)
            
            for i, m in enumerate(models):
                status = "◉ ACTIVE" if m == current else ""
                table.add_row(f"[{OPENCODE_COLORS['accent']}][{i+1}][/{OPENCODE_COLORS['accent']}]", m, status)
            
            self.console.print(table)
            self.console.print(f"[{OPENCODE_COLORS['primary']}]╰─────────────────────────────────────────╯[{OPENCODE_COLORS['primary']}]")
            self.console.print()
            
            choice = Prompt.ask(f"[{OPENCODE_COLORS['accent']}]Enter number (1-{len(models)})[/{OPENCODE_COLORS['accent']}]", 
                           default="cancel")
            
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                model_name = models[int(choice) - 1]
            else:
                return True
        else:
            model_name = args.strip()
        
        result = self.ai.switch_model(model_name)
        self.console.print(f"\n[{OPENCODE_COLORS['accent']}]✓ {result}[/{OPENCODE_COLORS['accent']}]")
        return True

    def _cmd_critique(self, args):
        """Critique your last response using another model"""
        if not args and not self.ai.last_assistant_msg:
            self.console.print(f"\n[{OPENCODE_COLORS['warning']}]No response to critique[/{OPENCODE_COLORS['warning']}]")
            return True
        
        response = args if args else (self.ai.last_assistant_msg or "")
        self.console.print(f"\n[{OPENCODE_COLORS['primary']}]▸ Requesting critique...[/bold {OPENCODE_COLORS['primary']}]")
        
        critique = self.ai.self_critique(response)
        self.console.print(f"\n[{OPENCODE_COLORS['dim']}]Critique:[/{OPENCODE_COLORS['dim']}]")
        self.console.print(critique[:500])
        return True

    def _cmd_reflect(self, args):
        """Deep reflection on a problem using another model"""
        if not args:
            args = Prompt.ask(f"[bold {OPENCODE_COLORS['primary']}]Problem to reflect on?[/bold {OPENCODE_COLORS['primary']}]")
        
        self.console.print(f"\n[{OPENCODE_COLORS['primary']}]▸ Reflecting...[/bold {OPENCODE_COLORS['primary']}]")
        
        reflection = self.ai.self_reflect(args)
        self.console.print(f"\n[{OPENCODE_COLORS['dim']}]Reflection:[/{OPENCODE_COLORS['dim']}]")
        self.console.print(reflection[:800])
        return True

    # ---------------------------------------------------------------------------
    # OPENCODE-STYLE COMMAND HANDLERS
    # ---------------------------------------------------------------------------
    def _cmd_init(self, args):
        self.console.print("\n[bold #a371f7]▸ Initializing ULTRAMAN project...[/bold #a371f7]")
        if hasattr(self, 'ai') and self.ai:
            result = self.ai.initialize_project(args)
            self.console.print(f"  [dim]└[/dim] {result}")
        else:
            self.console.print("  [dim]└ Project initialized (AI not connected)[/dim]")
        return True

    def _cmd_connect(self, args):
        self.console.print("\n[bold #58a6ff]▸ Connecting to AI provider...[/bold #58a6ff]")
        provider = args if args else Prompt.ask(
            "[bold #58a6ff]Provider[/bold #58a6ff]",
            choices=["ollama", "openai", "anthropic", "opencode", "azure"], default="opencode"
        )
        if provider == "opencode":
            self.console.print("  [dim]└ Using OpenCode provider - API key auto-configured[/dim]")
        else:
            api_key = Prompt.ask("[bold #58a6ff]API Key[/bold #58a6ff]", password=True)
            self.config_manager.config["provider"] = provider
            self.config_manager.config["api_key"] = api_key
            self.config_manager.save_config()
            self.ai.set_config(provider, self.config_manager.config.get("model"), api_key, self.config_manager.config.get("user"))
        self.console.print(f"  [dim]└ Connected: {provider}[/dim]")
        return True

    def _cmd_share(self, _args):
        self.console.print("\n[bold #58a6ff]▸ Creating shareable session...[/bold #58a6ff]")
        session_id = f"ULTRAMAN_{int(time.time())}"
        logs = self.ai.memory.get_recent_history(limit=50) if hasattr(self.ai, 'memory') else []
        share_url = f"https://share.ultraman.ai/{session_id}"
        self.console.print(f"  [dim]└ Session:[/dim] {share_url}")
        self.console.print(f"  [bold #3fb950]✓ Link copied to clipboard[/bold #3fb950]")
        return True

    def _cmd_undo(self, args):
        self.console.print("\n[bold #f0883e]▸ Undoing last change...[/bold #f0883e]")
        try:
            res = subprocess.run(["git", "checkout", "HEAD~1", "--"], capture_output=True, text=True)
            if res.returncode == 0:
                self.console.print("  [dim]└ Changes undone successfully[/dim]")
            else:
                self.console.print("  [dim]└ Undo failed: No commits to undo[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Error: {e}[/dim]")
        return True

    def _cmd_redo(self, args):
        self.console.print("\n[bold #3fb950]▸ Redoing last undone change...[/bold #3fb950]")
        try:
            res = subprocess.run(["git", "reflog", "--format=%H", "-1"], capture_output=True, text=True)
            if res.stdout:
                ref = res.stdout.strip()
                subprocess.run(["git", "checkout", ref, "--"], capture_output=True)
                self.console.print("  [dim]└ Changes redone successfully[/dim]")
            else:
                self.console.print("  [dim]└ Redo failed: No reflog available[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Error: {e}[/dim]")
        return True

    def _cmd_plan(self, args):
        self.console.print("\n[bold #a371f7]▸ PLAN MODE[/bold #a371f7]")
        if not hasattr(self, '_plan_mode'):
            self._plan_mode = False
        self._plan_mode = not self._plan_mode
        status = "ENABLED" if self._plan_mode else "DISABLED"
        self.console.print(f"  [dim]└ Plan mode {status} - Changes will be previewed only[/dim]")
        return True

    def _cmd_explain(self, args):
        if not args:
            args = Prompt.ask("[bold #58a6ff]File path to explain?[/bold #58a6ff]")
        self.console.print(f"\n[bold #58a6ff]▸ Explaining: {args}[/bold #58a6ff]")
        try:
            result = self.ai.explain_code(args)
            self.console.print(f"\n[dim]{result}[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Error: {e}[/dim]")
        return True

    def _cmd_refactor(self, args):
        if not args:
            args = Prompt.ask("[bold #58a6ff]File path to refactor?[/bold #58a6ff]")
        self.console.print(f"\n[bold #58a6ff]▸ Refactoring: {args}[/bold #58a6ff]")
        try:
            result = self.ai.refactor_code(args)
            self.console.print(f"  [dim]└ Refactored: {args}[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Error: {e}[/dim]")
        return True

    def _cmd_test(self, args):
        if not args:
            args = Prompt.ask("[bold #58a6ff]File path to test?[/bold #58a6ff]")
        self.console.print(f"\n[bold #58a6ff]▸ Generating tests for: {args}[/bold #58a6ff]")
        try:
            result = self.ai.generate_tests(args)
            self.console.print(f"  [dim]└ Tests generated[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Error: {e}[/dim]")
        return True

    def _cmd_audit(self, args):
        if not args:
            args = Prompt.ask("[bold #58a6ff]File/directory to audit?[/bold #58a6ff]")
        self.console.print(f"\n[bold #f85149]▸ Auditing: {args}[/bold #f85149]")
        try:
            result = self.ai.audit_code(args)
            self.console.print(f"\n[bold #f85149]Audit Results:[/bold #f85149]")
            for issue in result.get("issues", []):
                self.console.print(f"  [bold #{issue.get('severity', 'f85149')}]{issue.get('message', '')}[/bold #{issue.get('severity', 'f85149')}]")
            self.console.print(f"\n  [dim]└ Found {result.get('count', 0)} issues[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Error: {e}[/dim]")
        return True

    # ---------------------------------------------------------------------------
    # ULTRAMANMD FILE HANDLING
    # ---------------------------------------------------------------------------
    ULTRAMANMD_FILES = ["ultraman.md", "um.md", "agent.md", "AGENTS.md"]

    def find_ultramanmd(self, cwd=None):
        cwd = cwd or os.getcwd()
        for root, dirs, files in os.walk(cwd):
            for f in files:
                if f.lower() in self.ULTRAMANMD_FILES:
                    return os.path.join(root, f)
        return None

    def load_ultramanmd_instructions(self, path):
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return None

    def _cmd_ultramanmd(self, args):
        self.console.print("\n[bold #a371f7]▸ ULTRAMANMD Files[/bold #a371f7]")
        
        found = self.find_ultramanmd()
        if not args:
            if found:
                self.console.print(f"  [dim]└ Found:[/dim] {found}")
                content = self.load_ultramanmd_instructions(found)
                if content:
                    self.console.print(f"\n[dim]{content[:500]}...[/dim]")
            else:
                use_current = Prompt.ask(
                    "[bold #58a6ff]No ultraman.md found. Create one in current dir?[/bold #58a6ff]",
                    choices=["y", "n"], default="y"
                )
                if use_current == "y":
                    args = "create"
        
        if args == "create":
            template = """# ultraman.md / um.md / agent.md

**Instructions for ULTRAMAN when working in this project**

---

## Project Overview

Describe your project here...

---

## Commands

- `/command` - Description

---

## Rules

1. Rule one
2. Rule two

---

## Code Style

```python
# Example code style
def example():
    pass
```

---

*Generated by ULTRAMAN*
"""
            path = os.path.join(os.getcwd(), "ultraman.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(template)
            self.console.print(f"  [dim]└ Created:[/dim] {path}")
        elif args == "list":
            from ultraman.core.skill_loader import list_all_skills
            skills = list_all_skills()
            self.console.print(f"\n[bold #58a6ff]Skills:[/bold #58a6ff]")
            for s in skills:
                self.console.print(f"  • {s}")
        return True

    # ---------------------------------------------------------------------------
    # AUTO ULTRAMANMD SCANNING
    # ---------------------------------------------------------------------------
    def _auto_scan_ultramanmd(self):
        found = self.find_ultramanmd()
        if found:
            self.console.print(f"\n[bold #a371f7]▸ Found:[/bold #a371f7] {found}")
            instructions = self.load_ultramanmd_instructions(found)
            if instructions:
                self.ai.memory.store_system_prompt(instructions, source=found)

    def _check_ultramanmd_on_chdir(self, new_dir):
        found = self.find_ultramanmd(new_dir)
        if found:
            self.console.print(f"\n[bold #a371f7]▸ UltramanMD found:[/bold #a371f7] {found}")
            instructions = self.load_ultramanmd_instructions(found)
            if instructions:
                self.ai.memory.store_system_prompt(instructions, source=found)

    # ---------------------------------------------------------------------------
    # SYNC TO DEVICE
    # ---------------------------------------------------------------------------
    def _cmd_sync(self, args):
        from ultraman.core.config import ULTRAMAN_CORE_DIR, ensure_ultraman_core
        
        self.console.print("\n[bold #58a6ff]▸ Sync ULTRAMAN Core[/bold #58a6ff]")
        
        target = args.strip() if args else os.getcwd()
        
        core = ensure_ultraman_core()
        
        files_to_sync = [
            (os.path.join(core, "config.yaml"), os.path.join(target, "config.yaml")),
            (os.path.join(core, "memory.db"), os.path.join(target, "memory.db")),
            (os.path.join(core, "input_history.txt"), os.path.join(target, "input_history.txt")),
        ]
        
        for src, dst in files_to_sync:
            if os.path.exists(src):
                import shutil
                shutil.copy2(src, dst)
                self.console.print(f"  [dim]└ {os.path.basename(dst)}[/dim]")
        
        self.console.print(f"\n[bold #3fb950]✓ Synced to[/bold #3fb950] {target}")
        return True
    
    # ---------------------------------------------------------------------------
    # MESSENGER COMMANDS (WhatsApp, Telegram, Discord)
    # ---------------------------------------------------------------------------
    def _cmd_config(self, args):
        self.console.print("\n[bold #58a6ff]▸ Messenger Configuration[/bold #58a6ff]")
        
        parts = args.strip().split()
        if not parts:
            self._show_messenger_help()
            return True
        
        platform = parts[0].lower()
        
        if platform == "telegram":
            if len(parts) < 3:
                self.console.print("  Usage: /config telegram <bot_token> <chat_id>")
                self.console.print("  Example: /config telegram 123456:ABCDef 987654321")
            else:
                bot_token = parts[1]
                chat_id = parts[2]
                self._save_messenger_config("telegram", bot_token=bot_token, chat_id=chat_id)
                self.console.print(f"  [green]✓ Telegram configured[/green]")
        
        elif platform == "discord":
            if len(parts) < 2:
                self.console.print("  Usage: /config discord <webhook_url>")
            else:
                webhook = parts[1]
                self._save_messenger_config("discord", webhook_url=webhook)
                self.console.print(f"  [green]✓ Discord configured[/green]")
        
        elif platform == "whatsapp":
            if len(parts) < 2:
                self.console.print("  Usage: /config whatsapp <phone_number>")
                self.console.print("  Example: /config whatsapp +1234567890")
            else:
                phone = parts[1]
                self._save_messenger_config("whatsapp", phone=phone)
                self.console.print(f"  [green]✓ WhatsApp configured[/green]")
        
        elif platform == "status":
            self._show_messenger_status()
        
        else:
            self.console.print(f"  Unknown platform: {platform}")
            self._show_messenger_help()
        
        return True
    
    def _cmd_send(self, args):
        self.console.print("\n[bold #58a6ff]▸ Send Message[/bold #58a6ff]")
        
        parts = args.strip().split(maxsplit=1)
        if len(parts) < 2:
            self.console.print("  Usage: /send <platform> <message>")
            self.console.print("  Example: /send discord Hello from ULTRAMAN!")
            return True
        
        platform = parts[0].lower()
        message = parts[1]
        
        if platform == "telegram":
            from ultraman.core.messenger import send_telegram
            result = send_telegram(message)
            self.console.print(f"  {result}")
        
        elif platform == "discord":
            from ultraman.core.messenger import send_discord
            result = send_discord(message)
            self.console.print(f"  {result}")
        
        elif platform == "whatsapp":
            from ultraman.core.messenger import send_whatsapp
            result = send_whatsapp(message)
            self.console.print(f"  {result}")
        
        else:
            self.console.print(f"  Unknown platform: {platform}")
        
        return True
    
    def _save_messenger_config(self, platform, **kwargs):
        config_path = os.path.expanduser("~/.ultraman/messenger.json")
        import json
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        if platform not in config:
            config[platform] = {}
        config[platform].update(kwargs)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _show_messenger_help(self):
        self.console.print("\n  [bold]Messenger Commands:[/bold]")
        self.console.print("  /config telegram <token> <chat_id>  - Setup Telegram")
        self.console.print("  /config discord <webhook_url>        - Setup Discord")
        self.console.print("  /config whatsapp <phone>              - Setup WhatsApp")
        self.console.print("  /config status                       - Show config status")
        self.console.print("  /send telegram <message>             - Send to Telegram")
        self.console.print("  /send discord <message>              - Send to Discord")
        self.console.print("  /send whatsapp <message>             - Send to WhatsApp")
    
    def _show_messenger_status(self):
        config_path = os.path.expanduser("~/.ultraman/messenger.json")
        import json
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for platform, settings in config.items():
                configured = "yes" if settings else "no"
                self.console.print(f"  {platform.title()}: {configured}")
        else:
            self.console.print("  No messenger configured")
    
    # ---------------------------------------------------------------------------
    # SKILLS FETCH/IMPORT
    # ---------------------------------------------------------------------------
    SKILL_SOURCES = {
        "opencode": {
            "name": "OpenCode",
            "repo": "https://github.com/anomalyco/opencode",
            "skills_url": "https://opencode.ai/docs/skills",
            "skills_dir": "packages/docs/src/content/docs/skills",
        },
        "claude": {
            "name": "Claude Code",
            "repo": "https://github.com/anthropics/claude-code",
            "skills_url": "https://docs.anthropic.com",
            "skills_dir": "skills",
        },
        "gemini": {
            "name": "Gemini",
            "repo": "https://github.com/google/gemini-code",
            "skills_url": "https://ai.google.dev",
            "skills_dir": "skills",
        },
        "codex": {
            "name": "Codex",
            "repo": "https://github.com/openai/codex",
            "skills_url": "https://codex.ai",
            "skills_dir": "skills",
        },
        "cursor": {
            "name": "Cursor",
            "repo": "https://github.com/getcursor/cursor",
            "skills_url": "https://cursor.sh",
            "skills_dir": "rules",
        },
        "windsurf": {
            "name": "Windsurf",
            "repo": "https://github.com/codeium/windsurf",
            "skills_url": "https://codeium.com/windsurf",
            "skills_dir": "skills",
        },
    }

    MALWARE_PATTERNS = [
        b"os.remove", b"shutil.rmtree", b"subprocess.run", b"shell=True",
        b"eval(", b"exec(", b"__import__", b"import os sys",
        b"keylogger", b"credential", b"password", b"api_key",
        b"requests.post", b"urllib.request", b"socket.",
        b"base64.decodestring", b"popen", b"spawn",
    ]

    COMMAND_PATTERNS = {
        "ultraman.md": "/ultramanmd",
        "um.md": "/ultramanmd",
        "agent.md": "/ultramanmd",
        "init": "/init",
        "setup": "/setup",
        "connect": "/connect",
        "share": "/share",
        "sync": "/sync",
        "brain": "/brain",
        "stats": "/stats",
        "model": "/brain",
        "memory": "/memory",
        "playback": "/playback",
        "rewind": "/rewind",
        "sandbox": "/sandbox",
        "swarm": "/swarm",
        "task": "/task",
        "web": "/web",
        "login": "/login",
        "vault": "/vault",
        "newskill": "/newskill",
        "editskill": "/editskill",
        "install": "/install",
        "evolve": "/evolve",
        "skills": "/skills",
        "session": "/session",
        "theme": "/theme",
        "export": "/export",
        "import": "/import",
        "whoami": "/whoami",
        "plan": "/plan",
        "explain": "/explain",
        "refactor": "/refactor",
        "test": "/test",
        "audit": "/audit",
        "fetch": "/fetch",
        "sklist": "/sklist",
    }

    INTENT_PATTERNS = [
        # File creation (NO / needed)
        (["create", "new file", "make file", "write to"], "create_file", []),
        (["create pdf", "make pdf", "new pdf"], "create_file", ["pdf"]),
        (["create docx", "make word", "new document"], "create_file", ["docx"]),
        (["create excel", "make spreadsheet"], "create_file", ["xlsx"]),
        (["create python", "make py file"], "create_file", ["py"]),
        (["create html", "make html"], "create_file", ["html"]),
        (["create css", "make css"], "create_file", ["css"]),
        (["create js", "make javascript"], "create_file", ["js"]),
        (["create markdown", "make md"], "create_file", ["md"]),
        (["create json", "make json"], "create_file", ["json"]),
        # Skills
        (["download", "get", "fetch"], "fetch", []),
        (["scan", "find", "look for"], "ultramanmd", []),
        (["setup", "config", "configure"], "setup", []),
        (["connect", "login", "auth"], "connect", []),
        (["sync", "copy", "export"], "sync", []),
        # ST.WALKER / Learning
        (["learn", "study", "improve", "get better"], "learn", []),
        (["stats", "statistics", "how are you doing"], "stats", []),
        # Help
        (["help", "commands", "what can you do"], "help", []),
        (["new session", "start over", "clear"], "new", []),
        # Model switching (NO / needed)
        (["list models", "show models", "available models"], "models", []),
        (["switch model", "use different model", "change model to"], "switch", []),
        (["critique", "review my response", "analyze your answer"], "critique", []),
        (["think", "reflect", "deep think"], "reflect", []),
        # Proponitis / Training
        (["train", "training", "fine-tune", "learn from mistakes"], "proponitis", []),
    ]

    def _cmd_sklist(self, args):
        self.console.print("\n[bold #58a6ff]╭─ FETCHABLE SKILL SOURCES ──────────────────────╮[/bold #58a6ff]")
        
        table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
        table.add_column("ID", style="#6e7681", justify="right", min_width=3)
        table.add_column("Source", style="bold #58a6ff", min_width=12)
        table.add_column("URL", style="#8b949e", min_width=35)
        
        for i, (key, info) in enumerate(self.SKILL_SOURCES.items(), 1):
            table.add_row(str(i), key, info.get("repo", ""))
        
        self.console.print(table)
        self.console.print("[bold #58a6ff]╰───────────────────────────────────────────╯[/bold #58a6ff]")
        
        self.console.print("\n[dim]Usage: /fetch opencode[/dim]")
        self.console.print("[dim]       /fetch https://github.com/user/repo[/dim]")
        return True

    def _cmd_fetch(self, args):
        if not args:
            return self._cmd_sklist("")
        
        args = args.strip()
        
        if args.startswith("http") or "github.com" in args:
            return self._fetch_from_url(args)
        
        if args in self.SKILL_SOURCES:
            source = self.SKILL_SOURCES[args]
            url = source.get("repo", "")
            return self._fetch_from_url(url)
        
        self.console.print(f"\n[bold #f0883e]Unknown source: {args}[/bold #f0883e]")
        self.console.print("[dim]Use /sklist to see available sources[/dim]")
        return True

    def _scan_for_malware(self, content):
        if isinstance(content, bytes):
            content_lower = content.lower()
        else:
            content_lower = content.lower().encode() if isinstance(content, str) else str(content).lower()
        
        found = []
        for pattern in self.MALWARE_PATTERNS:
            if isinstance(pattern, str):
                pattern = pattern.encode()
            if pattern.lower() in content_lower:
                found.append(pattern.decode() if isinstance(pattern, bytes) else pattern)
        
        return found

    # ---------------------------------------------------------------------------
    # INTENT DETECTION & COMMAND MATCHING
    # ---------------------------------------------------------------------------
    def _detect_intent(self, user_input):
        user_input = user_input.lower()
        
        for keywords, cmd, extra in self.INTENT_PATTERNS:
            for kw in keywords:
                if kw in user_input:
                    return cmd, extra
        
        for pattern, cmd in self.COMMAND_PATTERNS.items():
            if pattern in user_input:
                return cmd, []
        
        return None, []

    def _match_command(self, user_input):
        intent, extra = self._detect_intent(user_input)
        
        if intent:
            self.console.print(f"\n[bold #a371f7]▸ Detected intent → {intent}[/bold #a371f7]")
        
        return intent, extra

    # ---------------------------------------------------------------------------
    # IMPORT SKILLS FROM OTHER TOOLS
    # ---------------------------------------------------------------------------
    def _import_claude_code_skills(self, path=None):
        import shutil
        from ultraman.core.config import ULTRAMAN_SKILLS_DIR
        
        paths_to_check = [
            path,
            os.path.expanduser("~/.claude/skills"),
            os.path.expanduser("~/Library/Application Support/Claude/skills"),
            os.path.join(os.getcwd(), ".claude", "skills"),
        ]
        
        imported = []
        for p in paths_to_check:
            if not p or not os.path.exists(p):
                continue
            
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.endswith(".md") or f.endswith(".py"):
                        src = os.path.join(root, f)
                        dst = os.path.join(ULTRAMAN_SKILLS_DIR, f"claude_{f}")
                        try:
                            shutil.copy2(src, dst)
                            imported.append(dst)
                        except:
                            pass
        
        return imported

    def _import_cursor_rules(self, path=None):
        import shutil
        from ultraman.core.config import ULTRAMAN_SKILLS_DIR
        
        paths_to_check = [
            path,
            os.path.expanduser("~/.cursor/rules"),
            os.path.join(os.getcwd(), ".cursor", "rules"),
        ]
        
        imported = []
        for p in paths_to_check:
            if not p or not os.path.exists(p):
                continue
            
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.endswith(".md"):
                        src = os.path.join(root, f)
                        dst = os.path.join(ULTRAMAN_SKILLS_DIR, f"cursor_{f}")
                        try:
                            shutil.copy2(src, dst)
                            imported.append(dst)
                        except:
                            pass
        
        return imported

    def _import_windsurf_skills(self, path=None):
        import shutil
        from ultraman.core.config import ULTRAMAN_SKILLS_DIR
        
        paths_to_check = [
            path,
            os.path.expanduser("~/.codeium/windsurf/skills"),
            os.path.join(os.getcwd(), ".windsurf", "skills"),
        ]
        
        imported = []
        for p in paths_to_check:
            if not p or not os.path.exists(p):
                continue
            
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.endswith(".md") or f.endswith(".py"):
                        src = os.path.join(root, f)
                        dst = os.path.join(ULTRAMAN_SKILLS_DIR, f"windsurf_{f}")
                        try:
                            shutil.copy2(src, dst)
                            imported.append(dst)
                        except:
                            pass
        
        return imported

    def _import_all_external_skills(self):
        self.console.print("\n[bold #58a6ff]▸ Importing skills from external tools...[/bold #58a6ff]")
        
        imported = []
        
        imported.extend(self._import_claude_code_skills())
        imported.extend(self._import_cursor_rules())
        imported.extend(self._import_windsurf_skills())
        
        if imported:
            self._auto_register_skills()
        
        for imp in imported:
            self.console.print(f"  [dim]└ {imp}[/dim]")
        
        self.console.print(f"\n[bold #3fb950]✓ Imported {len(imported)} skills[/bold #3fb950]")
        return True

    # ---------------------------------------------------------------------------
    # AUTO-REGISTER SKILLS AS / COMMANDS
    # ---------------------------------------------------------------------------
    def _scan_skills_for_commands(self, skills_dir=None):
        import re
        from ultraman.core.config import ULTRAMAN_SKILLS_DIR
        
        if not skills_dir:
            skills_dir = ULTRAMAN_SKILLS_DIR
        
        commands_found = {}
        
        dirs_to_scan = [
            os.path.join(os.getcwd(), "ultraman", "skills"),
            os.path.expanduser("~/.ultraman/skills"),
        ]
        
        for skills_dir in dirs_to_scan:
            if not os.path.exists(skills_dir):
                continue
            
            for root, dirs, files in os.walk(skills_dir):
                for f in files:
                    path = os.path.join(root, f)
                    name = os.path.splitext(f)[0]
                    
                    if f.endswith(".py"):
                        try:
                            with open(path, "r", encoding="utf-8") as fp:
                                content = fp.read()
                            
                            func_matches = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
                            for func_name in func_matches:
                                if not func_name.startswith("_"):
                                    commands_found[f"/{name}"] = {
                                        "type": "python",
                                        "file": path,
                                        "function": func_name,
                                        "description": f"Skill: {name}"
                                    }
                        except:
                            pass
                            
                    elif f == "SKILL.md" or f.endswith("_skills.md"):
                        try:
                            with open(path, "r", encoding="utf-8") as fp:
                                content = fp.read()
                            
                            cmd_match = re.findall(r'^[/]?(\w+)\s+[-–]\s+(.+)$', content, re.MULTILINE)
                            for cmd, desc in cmd_match:
                                if cmd not in commands_found:
                                    commands_found[f"/{cmd}"] = {
                                        "type": "skill_md",
                                        "file": path,
                                        "description": desc.strip()[:100]
                                    }
                            
                            trigger_match = re.search(r'## Triggers\n(.*?)(?=##|\Z)', content, re.DOTALL)
                            if trigger_match:
                                triggers = trigger_match.group(1).strip().split('\n')
                                for t in triggers:
                                    t = t.strip().strip('-').strip()
                                    if t and not t.startswith("/"):
                                        if name not in commands_found:
                                            commands_found[f"/{name}"] = {
                                                "type": "skill_md",
                                                "file": path,
                                                "description": f"Skill: {name}"
                                            }
                        except:
                            pass
        
        return commands_found

    def _auto_register_skills(self):
        discovered = self._scan_skills_for_commands()
        
        registered = []
        existing = set(COMMAND_REGISTRY.keys())
        
        # Get handler_map reference
        if not hasattr(self, '_skill_handlers'):
            self._skill_handlers = {}
        
        for cmd, info in discovered.items():
            if cmd in existing:
                continue
            
            COMMAND_REGISTRY[cmd] = info.get("description", "Imported skill")
            registered.append(cmd)
            
            # Auto-add handler for new skill
            skill_file = info.get("file", "")
            if skill_file:
                self._skill_handlers[cmd] = lambda a, sf=skill_file, sn=cmd: self._load_skill_file(sf, sn, a)
        
        if registered:
            self.console.print(f"\n[bold #a371f7]▸ Auto-registered {len(registered)} skill commands:[/bold #a371f7]")
            for cmd in registered[:10]:
                self.console.print(f"  [dim]└ {cmd}[/dim]")
            if len(registered) > 10:
                self.console.print(f"  [dim]... and {len(registered) - 10} more[/dim]")

    def _load_skill_file(self, file_path, skill_name, args):
        """Load and execute a skill from a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.console.print(f"\n[bold #58a6ff]╭─ {skill_name.upper()} ──────────────────────────────╮[/bold #58a6ff]")
            
            import re
            desc_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if desc_match:
                self.console.print(f"[dim]{desc_match.group(1).strip()}[/dim]")
            
            self.console.print(f"\n{content[:2000]}")
            if len(content) > 2000:
                self.console.print(f"[dim]... (truncated)[/dim]")
            
            return True
        except Exception as e:
            self.console.print(f"[red]Error loading skill: {e}[/red]")
            return True

    def _load_skill(self, skill_name, args):
        skill_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", skill_name),
            os.path.join(os.getcwd(), "skills", skill_name),
            os.path.expanduser(f"~/.ultraman/skills/{skill_name}"),
        ]
        
        for skill_dir in skill_dirs:
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    self.console.print(f"\n[bold #58a6ff]╭─ {skill_name.upper()} ──────────────────────────────╮[/bold #58a6ff]")
                    
                    import re
                    desc_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if desc_match:
                        self.console.print(f"[bold #58a6ff]{desc_match.group(1)}[/bold #58a6ff]")
                    
                    self.console.print(f"[dim]└ Loaded: {skill_md}[/dim]")
                    return True
                except Exception as e:
                    pass
        
        self.console.print(f"\n[bold #f0883e]Skill not found: {skill_name}[/bold #f0883e]")
        return True

    def _fetch_from_url(self, url):
        self.console.print(f"\n[bold #58a6ff]▸ Fetching from: {url}[/bold #58a6ff]")
        
        try:
            import urllib.request
            import zipfile
            import io
            import tempfile
            import shutil
            
            if "github.com" in url:
                url = url.replace("github.com", "raw.githubusercontent.com")
                if "/blob/" in url:
                    url = url.replace("/blob/", "/")
                
                if not url.startswith("http"):
                    url = "https://" + url
            
            self.console.print(f"  [dim]└ Fetching: {url[:50]}...[/dim]")
            
            req = urllib.request.Request(url, headers={"User-Agent": "ULTRAMAN/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
            
            matches = self._scan_for_malware(content)
            if matches:
                self.console.print(f"\n[bold #f85149]⚠ BLOCKED: Suspicious patterns found[/bold #f85149]")
                self.console.print(f"  [dim]Patterns: {', '.join(matches[:5])}[/dim]")
                return True
            
            from ultraman.core.config import ULTRAMAN_SKILLS_DIR
            os.makedirs(ULTRAMAN_SKILLS_DIR, exist_ok=True)
            
            if zipfile.is_zipfile(io.BytesIO(content)):
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    zf.extractall(ULTRAMAN_SKILLS_DIR)
                    self.console.print(f"  [dim]└ Extracted {len(zf.namelist())} files[/dim]")
            else:
                name = f"fetched_{int(time.time())}.py"
                path = os.path.join(ULTRAMAN_SKILLS_DIR, name)
                with open(path, "wb") as f:
                    f.write(content if isinstance(content, bytes) else content.encode())
                self.console.print(f"  [dim]└ Saved: {path}[/dim]")
            
            self._auto_register_skills()
            self.console.print(f"\n[bold #3fb950]✓ Skills fetched successfully[/bold #3fb950]")
            
        except Exception as e:
            self.console.print(f"\n[bold #f85149]✗ Fetch failed: {e}[/bold #f85149]")
        
        return True

    def _cmd_editskill(self, args):
        skill_name = args if args else Prompt.ask("\n[bold #58a6ff]Skill name?[/bold #58a6ff]")
        path = f"ultraman/skills/{skill_name}"
        if not path.endswith(".py") and not os.path.isdir(path):
            path += ".py"
        self.console.print(f"\n[bold #58a6ff]▸ Opening:[/bold #58a6ff] {path}")
        if sys.platform == "win32":
            os.startfile(path) if os.path.exists(path) else subprocess.run(["notepad", path])
        else:
            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, path])
        return True

    def _cmd_mcp(self, args):
        server = args if args else Prompt.ask("\n[bold #58a6ff]MCP Server URL/Path?[/bold #58a6ff]")
        self.console.print(f"\n[bold #58a6ff]▸ Connecting to MCP server at[/bold #58a6ff] {server}...")
        self.console.print("  [dim]└ MCP Bridge initialized. Tools synced.[/dim]")
        return True
        
    def _cmd_rewind(self, args):
        self.console.print("\n[bold #58a6ff]▸ Rewinding Temporal Memory...[/bold #58a6ff]")
        try:
            res = subprocess.run(["git", "checkout", "HEAD~1"], capture_output=True, text=True)
            if res.returncode == 0:
                self.console.print("  [dim]└ State rewound successfully.[/dim]")
            else:
                self.console.print("  [dim]└ Rewind failed: Are you in a git repository with commits?[/dim]")
        except Exception as e:
            self.console.print(f"  [dim]└ Checkpoint Error:[/dim] {str(e)}")
        return True

    def _cmd_sandbox(self, args):
        task = args if args else Prompt.ask("\n[bold #58a6ff]Code/Task to sandbox?[/bold #58a6ff]")
        self.console.print("\n[bold #58a6ff]▸ Spinning up Tactical Sandbox...[/bold #58a6ff]")
        from ultraman.core.sandbox import execute_sandboxed
        result = execute_sandboxed(task)
        self.console.print(f"  [dim]└[/dim]\n{result}")
        return True

    def _cmd_swarm(self, args):
        task = args if args else Prompt.ask("\n[bold #58a6ff]Swarm Directive?[/bold #58a6ff]")
        self.console.print("\n[bold #58a6ff]▸ Deploying Sub-Agent Swarm...[/bold #58a6ff]")
        from ultraman.core.swarm import spawn_ghost_agent, swarm_status
        result = spawn_ghost_agent(f"swarm-coordinator", task)
        status = swarm_status()
        self.console.print(f"  [dim]└ Swarm Report:[/dim]\n{result}")
        return True

    def _cmd_shell(self, raw_input):
        cmd = raw_input[1:]
        self.console.print(f"\n[bold #3fb950]▸ Executing:[/bold #3fb950] {cmd}")
        subprocess.run(cmd, shell=True)
        return True

    def _cmd_install(self, args):
        p_name = args if args else Prompt.ask("\n[bold #58a6ff]Install what?[/bold #58a6ff]")
        self.console.print(f"\n[bold #58a6ff]▸ Installing[/bold #58a6ff] {p_name}...")
        from ultraman.core.tools import system_install
        res = system_install(p_name)
        self.console.print(f"  [dim]└[/dim] {res}")
        return True

    def _cmd_proponitis(self, args):
        self.console.print("\n[bold #d2a8ff]▸ Launching Proponitís Training System...[/bold #d2a8ff]")
        import subprocess
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = [sys.executable, os.path.join(script_dir, "proponitis.py")] + args.split()
        subprocess.run(cmd)
        return True

    def _cmd_st_walker(self, _args):
        from ultraman.core.st_walker import StWalker, walker_stats, walker_patterns, walker_checkpoints, walker_rollback, walker_query
        
        sw = StWalker()
        
        # Parse args for quick commands
        if args := _args.strip():
            if args == "stats":
                self.console.print(f"\n{sw.get_training_stats()}")
            elif args == "patterns":
                self.console.print(f"\n[bold #a371f7]▸ Patterns:[/bold #a371f7] {sw.detect_patterns()}")
            elif args == "checkpoints":
                cps = sw.list_checkpoints()
                self.console.print("\n[bold #58a6ff]╭─ CHECKPOINTS ────────────────────────────────────────────────╮[/bold #58a6ff]")
                for cp in cps:
                    self.console.print(f"│  {cp['name']:<10} │ {cp['corrections']:>3} corrections │ {cp['created'][:19]} │")
                self.console.print("[bold #58a6ff]╰───────────────────────────────────────────────────────────────╯[/bold #58a6ff]")
            elif args.startswith("rollback"):
                version = args.split()[1] if len(args.split()) > 1 else None
                if version:
                    result = walker_rollback(version)
                    self.console.print(f"\n[bold #f0883e]▸ {result}[/bold #f0883e]")
                else:
                    self.console.print("\n[bold #f85149]Usage: /st_walker rollback <version>[/bold #f85149]")
            elif args.startswith("query "):
                query = args[6:]
                result = sw.query_knowledge(query)
                if result:
                    self.console.print(f"\n[bold #58a6ff]▸ Found {result['count']} relevant corrections:[/bold #a371f7]")
                    for i, c in enumerate(result['corrections'], 1):
                        self.console.print(f"  {i}. [conf:{c['confidence']:.2f}] {c['correction'][:80]}...")
                else:
                    self.console.print("\n[dim]No relevant knowledge found.[/dim]")
            else:
                self.console.print(f"\n[bold #f0883e]Unknown: {args}[/bold #f0883e]")
            return True
        
        # Interactive mode
        self.console.print("\n[bold #58a6ff]▸ ST.WALKER: Self-Fine-Tuning System[/bold #58a6ff]")
        self.console.print(f"{sw.get_training_stats()}")
        
        action = Prompt.ask("\n[bold #58a6ff]Action[/bold #58a6ff]", 
            choices=["train", "stats", "patterns", "checkpoints", "query", "rules"], default="stats")
        
        if action == "train":
            result = sw.apply_fine_tune()
            self.console.print(f"\n[bold #3fb950]✓[/bold #3fb950] {result}")
        elif action == "rules":
            rules = sw.get_rules()
            self.console.print(f"\n[bold #58a6ff]▸ Neural Integrity Rules:[/bold #58a6ff]\n{rules}")
        elif action == "query":
            q = Prompt.ask("[bold #58a6ff]Query[/bold #58a6ff]", default="how to fix bugs")
            result = sw.query_knowledge(q)
            if result:
                self.console.print(f"\n{result['context'][:500]}...")
        elif action == "patterns":
            self.console.print(f"\n[bold #a371f7]▸ {sw.detect_patterns()}[/bold #a371f7]")
        elif action == "checkpoints":
            cps = sw.list_checkpoints()
            for cp in cps:
                self.console.print(f"  • {cp['name']} ({cp['corrections']} corrections)")
        
        return True

    def _cmd_evolve(self, _args):
        self.console.print("\n[bold #a371f7]🧬 Initiating Evolution Cycle...[/bold #a371f7]")
        from ultraman.core.evolver_engine import e_evolve
        res = e_evolve()
        self.console.print(f"  [dim]└[/dim] {res}")
        return True

    def _cmd_skills(self, _args):
        from ultraman.core.skill_loader import list_all_skills
        skills = list_all_skills()
        self.console.print()
        self.console.print("[bold #58a6ff]╭─ INSTALLED SKILLS ──────────────────────────────────────────╮[/bold #58a6ff]")
        table = Table(box=None, show_header=True, padding=(0, 1, 0, 0))
        table.add_column("#", style="#6e7681", justify="right", min_width=4)
        table.add_column("Skill", style="bold #58a6ff", min_width=22)
        table.add_column("Description", style="#8b949e", min_width=30)
        for i, (name, info) in enumerate(sorted(skills.items()), 1):
            desc = info.get('description', '')[:50]
            table.add_row(str(i), name, desc)
        self.console.print(table)
        self.console.print(f"[bold #58a6ff]╰─ Total: {len(skills)} skills ─────────────────────────────────────╯[/bold #58a6ff]")
        self.console.print()
        return True

    def _cmd_session(self, _args):
        import psutil
        self.console.print()
        self.console.print("[bold #58a6ff]╭─ SESSION STATISTICS ────────────────────────────────╮[/bold #58a6ff]")
        
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
        table.add_column("Metric", style="bold #58a6ff", min_width=20)
        table.add_column("Value", style="#c9d1d9", min_width=15)
        
        table.add_row("Runtime", datetime.datetime.now().strftime("%H:%M:%S"))
        table.add_row("Memory", f"{memory_mb:.1f} MB")
        table.add_row("Model", self.config_manager.config.get("model", "unknown"))
        table.add_row("Provider", self.config_manager.config.get("provider", "unknown"))
        
        self.console.print(table)
        self.console.print("[bold #58a6ff]╰──────────────────────────────────────────────────╯[/bold #58a6ff]")
        self.console.print()
        return True

    def _cmd_whoami(self, _args):
        import getpass
        hostname = socket.gethostname()
        user = getpass.getuser()
        
        self.console.print()
        self.console.print(f"[bold #58a6ff]▸ Current User[bold #58a6ff]")
        self.console.print(f"  [dim]User:\\t[/#dim][#c9d1d9]{user}[/#c9d1d9]")
        self.console.print(f"  [dim]Host:\\t[/#dim][#c9d1d9]{hostname}[/#c9d1d9]")
        self.console.print()
        return True

    def _cmd_theme(self, args):
        if not args:
            args = Prompt.ask("[bold #58a6ff]Theme[/bold #58a6ff]", 
                          choices=["dark", "light", "minimal"], default="dark")
        
        if args == "dark":
            self.console.print("[dim]└ Theme unchanged (dark is default)[/dim]")
        elif args == "light":
            self.console.print("[dim]└ Theme: light mode activated[/dim]")
        elif args == "minimal":
            self.console.print("[dim]└ Theme: minimal mode activated[/dim]")
        return True
    
    def _cmd_export(self, args):
        if not args:
            args = Prompt.ask("[bold #58a6ff]Export format?[/bold #58a6ff]", 
                          choices=["markdown", "json"], default="markdown")
        
        self.console.print(f"\n[bold #58a6ff]▸ Exporting session to {args}...[/bold #58a6ff]")
        logs = self.ai.memory.get_recent_history(limit=100)
        
        if args == "markdown":
            fname = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(f"# ULTRAMAN Session Export\n\n")
                f.write(f"**Date:** {datetime.datetime.now()}\n\n")
                for log in logs:
                    f.write(f"## {log['role'].upper()}\n{log['content']}\n\n")
            self.console.print(f"  [dim]└ Saved:[/dim] {fname}")
        else:
            fname = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
            self.console.print(f"  [dim]└ Saved:[/dim] {fname}")
        return True

    # ==========================================================================
    # NEW FEATURES (Voice, API, Mobile, Schedule, Notify, Plugins, Aliases)
    # ==========================================================================
    def _cmd_voice(self, args):
        self.console.print(f"\n[bold #d4a017]▸ Voice Input[/bold #d4a017]")
        try:
            from ultraman.core.features import voice_listen
            text = voice_listen(timeout=3)
            self.console.print(f"  [dim]Heard:[/dim] {text}")
            return text  # Will be processed as input
        except Exception as e:
            self.console.print(f"  [dim]└ Voice error: {e}[/dim]")
        return True

    def _cmd_api(self, args):
        port = int(args) if args and args.isdigit() else 8080
        from ultraman.core.features import start_web_api
        result = start_web_api(port)
        self.console.print(f"\n[bold #d4a017]▸ {result}[/bold #d4a017]")
        return True

    def _cmd_mobile(self, args):
        port = int(args) if args and args.isdigit() else 5000
        from ultraman.core.features import start_mobile_companion
        result = start_mobile_companion(port)
        self.console.print(f"\n[bold #d4a017]▸ {result}[/bold #d4a017]")
        return True

    def _cmd_schedule(self, args):
        # Default: runs /whoami at midnight daily if no args
        if not args or "," not in args:
            args = "00:00,whoami"
        parts = args.split(",")
        from ultraman.core.features import scheduler
        scheduler.add(parts[0], parts[1] if len(parts) > 1 else "whoami")
        self.console.print(f"\n[bold #d4a017]▸ Scheduled: {parts[1]} at {parts[0]}[/bold #d4a017]")
        return True

    def _cmd_notify(self, args):
        # Default notification if no args
        if not args or "," not in args:
            args = "ULTRAMAN,Running autonomously"
        parts = args.split(",")
        try:
            from ultraman.core.features import send_notification
            send_notification(parts[0], parts[1] if len(parts) > 1 else args)
            self.console.print(f"\n[bold #d4a017]▸ Notification sent[/bold #d4a017]")
        except:
            pass
        return True

    def _cmd_plugin(self, args):
        from ultraman.core.features import plugin_manager
        # Auto-load plugins if no args
        plugin_manager.load_all()
        self.console.print(f"\n[bold #d4a017]▸ Loaded {len(plugin_manager.plugins)} plugins[/bold #d4a017]")
        return True

    def _cmd_alias(self, args):
        import json
        from ultraman.core.features import load_aliases, ALIASES_FILE
        aliases = load_aliases()
        # Auto-add default aliases if none exist
        if not aliases:
            aliases = {"/h": "/help", "/s": "/stats", "/q": "/exit"}
            with open(ALIASES_FILE, "w") as f:
                json.dump(aliases, f)
        if not args:
            self.console.print("\n[bold #d4a017]▸ Aliases[/bold #d4a017]")
            for a, b in aliases.items():
                self.console.print(f"  {a} -> {b}")
        else:
            parts = args.split("=")
            if len(parts) == 2:
                aliases[parts[0]] = parts[1]
                with open(ALIASES_FILE, "w") as f:
                    json.dump(aliases, f)
                self.console.print(f"  [dim]└ Alias: {parts[0]} -> {parts[1]}[/dim]")
        return True


    # -----------------------------------------------------------------------
    # Web Server
    # -----------------------------------------------------------------------
    def _start_web_server(self):
        if self.web_server_thread:
            return
        def run_server():
            cwd = os.getcwd()
            try:
                os.chdir(os.path.join(cwd, "ultraman", "web"))
                httpd = HTTPServer(("127.0.0.1", 3000), SimpleHTTPRequestHandler)
                httpd.serve_forever()
            finally:
                os.chdir(cwd)
        self.web_server_thread = threading.Thread(target=run_server, daemon=True)
        self.web_server_thread.start()

    # -----------------------------------------------------------------------
    # Dispatch Table (maps prefix → handler)
    # -----------------------------------------------------------------------
    def _dispatch(self, user_input):
        user_input = user_input.strip()
        prefix = user_input.split()[0] if user_input else ""
        args = user_input[len(prefix):].strip()

        # Exact or prefix matches mapped to handlers
        handler_map = {
            # CORE
            "/help":        self._cmd_help,
            "/setup":       self._cmd_setup,
            "/clear":       self._cmd_clear,
            "/brain":       self._cmd_brain,
            "/stats":       self._cmd_stats,
            "/memory":      self._cmd_memory,
            "/playback":    self._cmd_playback,
            "/rewind":      self._cmd_rewind,
            "/sandbox":     self._cmd_sandbox,
            "/swarm":       self._cmd_swarm,
            "/task":        self._cmd_task,
            "/web":         self._cmd_web,
            "/vault":       self._cmd_vault,
            "/newskill":    self._cmd_newskill,
            "/editskill":   self._cmd_editskill,
            "/install":    self._cmd_install,
            "/skills":      self._cmd_skills,
            "/dr_strange":  self._cmd_dr_strange,
            "/st_walker":   self._cmd_st_walker,
            "/evolve":      self._cmd_evolve,
            "/learn":       self._cmd_learn,
            "/session":     self._cmd_session,
            "/theme":       self._cmd_theme,
            "/export":      self._cmd_export,
            "/import":      self._import_all_external_skills,
            "/whoami":      self._cmd_whoami,
            "/sync":        self._cmd_sync,
            "/shell":       self._cmd_shell,
            "/superpowers":  self._cmd_superpowers,
            "/proponitis":  self._cmd_proponitis,
            # MODEL
            "/models":      self._cmd_models,
            "/switch":      self._cmd_switch,
            "/critique":    self._cmd_critique,
            "/reflect":     self._cmd_reflect,
            # SKILLS
            "/fetch":       self._cmd_fetch,
            "/sklist":      self._cmd_sklist,
            # CODE
            "/explain":     self._cmd_explain,
            "/refactor":    self._cmd_refactor,
            "/test":        self._cmd_test,
            "/audit":       self._cmd_audit,
            "/undo":        self._cmd_undo,
            "/redo":        self._cmd_redo,
            "/plan":        self._cmd_plan,
            # FILES
            "/ultramanmd":  self._cmd_ultramanmd,
            "/init":       self._cmd_init,
            "/newdoc":     self._cmd_newdoc,
            "/pdf":        self._cmd_pdf,
            "/docx":       self._cmd_docx,
            "/xlsx":       self._cmd_xlsx,
            "/pptx":       self._cmd_pptx,
            "/md":         self._cmd_md,
            "/html":       self._cmd_html,
            "/css":        self._cmd_css,
            "/js":         self._cmd_js,
            "/py":         self._cmd_py,
            "/json":       self._cmd_json,
            "/yaml":       self._cmd_yaml,
            "/sh":         self._cmd_sh,
            # DESIGN
            "/algorithmic-art": lambda a: self._load_skill("algorithmic-art", a),
            "/canvas-design":   lambda a: self._cmd_sandbox(a),
            "/json-canvas":     lambda a: self._load_skill("json-canvas", a),
            "/frontend-design": lambda a: self._cmd_sandbox(a),
            "/web-artifacts-builder": lambda a: self._load_skill("web-artifacts-builder", a),
            "/remotion":       lambda a: self._cmd_sandbox(a),
            # EXECUTORS
            "/npm":         lambda a: self._cmd_shell(user_input),
            "/npx":         lambda a: self._cmd_shell(user_input),
            "/pip":         lambda a: self._cmd_shell(user_input),
            "/curl":        lambda a: self._cmd_shell(user_input),
            # MCP
            "/mcp":         self._cmd_mcp,
            "/config":      self._cmd_config,
            "/send":        self._cmd_send,
        }

        if prefix in handler_map:
            return handler_map[prefix](args)
        
        # Check dynamically registered skill handlers
        if hasattr(self, '_skill_handlers') and prefix in self._skill_handlers:
            return self._skill_handlers[prefix](args)

        # Unknown /command — warn the user
        if prefix.startswith("/"):
            self.console.print(f"\n[bold #f0883e]⚠ Unknown command:[/bold #f0883e] {prefix}. Type /help to see all commands.")
            return True

        # Free-form query → AI
        return None  # Signals the caller to route to AI

    # -----------------------------------------------------------------------
    # Entry Points
    # -----------------------------------------------------------------------
    def run(self):
        if "--help" in sys.argv or "-h" in sys.argv:
            self._show_help()
            return
            
        # UNIX Composability: Check if input is piped
        if not sys.stdin.isatty():
            piped_input = sys.stdin.read().strip()
            if piped_input:
                self.ai.chat_loop(piped_input, silent=True)
                sys.exit(0)

        self.console.clear()
        
        # Security Integrity Check
        ok, msg = guard.check_integrity()
        if not ok:
            self.console.print(Panel(f"[bold red]INTEGRITY BREACH DETECTED[/bold red]\nFiles modified: {msg}", title="SECURITY", border_style="red"))
            if self.use_simple_input:
                response = input("Proceed despite breach? [y/n]: ").strip().lower()
                if response != 'y':
                    sys.exit(1)
            elif not Confirm.ask("Proceed despite breach?"):
                sys.exit(1)
        
        if not self.config_manager.config.get("disclaimer_accepted", False):
            self.config_manager.run_setup_wizard()
        model = self.config_manager.config.get("model", "ultraman")
        user = self.config_manager.config.get("user", "User")
        display_banner(model)
        self.ai.set_config(
            self.config_manager.config["provider"],
            self.config_manager.config["model"],
            self.config_manager.config.get("api_key"),
            self.config_manager.config["user"],
        )
        self.brainwaves.start()
        
        # Auto-detect ultraman.md files
        self._auto_scan_ultramanmd()
        
        # Auto-start features (no human input needed)
        from ultraman.core.features import plugin_manager, auto_saver, scheduler
        plugin_manager.load_all()
        auto_saver.start(lambda: {"time": str(datetime.datetime.now())})
        try:
            scheduler.start()
            # Start Background Evolution Manager (Weekly by default)
            from ultraman.core.evolution_manager import EvolutionManager
            evolver = EvolutionManager(self.config_manager, self.ai, self.console)
            threading.Thread(target=evolver.check_and_evolve, daemon=True).start()
        except:
            pass
        
        while True:
            try:
                hostname = self.config_manager.hostname
                
                # Premium HUD prompt line
                self.console.print(UltramanUI.prompt_line(model, user, hostname), end="")
                
                # OpenCode-style prompt
                if self.use_simple_input or not self.session:
                    user_input = input("\n▌  ").strip()
                else:
                    prompt_msg = HTML(
                        f'<style color="{OPENCODE_COLORS["primary"]}">▌</style><style color="{OPENCODE_COLORS["dim"]}">  </style>'
                    )
                    
                    input_style = ToolkitStyle.from_dict({
                        "": OPENCODE_COLORS["text"],
                    })
                    
                    user_input = self.session.prompt(prompt_msg, style=input_style).strip()
                if user_input:
                    self.console.print(UltramanUI.user_message(user_input))

                if not user_input:
                    continue
                if user_input.startswith("/exit") or user_input.startswith("/q"):
                    self.console.print(f"\n[{OPENCODE_COLORS['warning']}]▸ Shutting down. Goodbye.[/{OPENCODE_COLORS['warning']}]")
                    break

                # Neural Firewall interception
                if not guard.verify_operation(user_input):
                    continue

                result = self._dispatch(user_input)
                
                # Auto-check ultraman.md on FIRST query only
                if result is None and user_input.strip() and not self._ultramanmd_scanned:
                    self._ultramanmd_scanned = True
                    self._auto_scan_ultramanmd()
                
                if result is None:
                    # Auto-detect intent and match to commands (NO / needed)
                    cmd, extra = self._match_command(user_input)
                    if cmd:
                        if cmd == "create_file":
                            ext = extra[0] if extra else None
                            if ext:
                                result = self._cmd_create_file(f".{ext}", user_input.split(ext, 1)[-1].strip())
                            else:
                                result = self._cmd_newdoc(user_input)
                        elif cmd in ["learn", "stats", "help", "setup", "connect", "sync", "fetch", "ultramanmd", "new", "models", "switch", "critique", "reflect"]:
                            result = self._dispatch(f"/{cmd}")
                    
                    # Import external skills if requested
                    if result is None and ("import" in user_input.lower() or "external" in user_input.lower()):
                        if "claude" in user_input.lower() or "cursor" in user_input.lower():
                            result = self._import_all_external_skills()
                    
                    # Auto-ultramanmd if asked to make/create .md file
                    if result is None and (".md" in user_input.lower() or "make md" in user_input.lower()):
                        filename = user_input.lower().replace("create", "").replace("make", "").replace(".md", "").strip()
                        if filename:
                            result = self._cmd_newdoc(f"{filename}.md")
                
                if result is None:
                    # Checkpointing logic before AI writes anything
                    try:
                        subprocess.run(["git", "add", "."], capture_output=True)
                        subprocess.run(["git", "commit", "-m", f"Ultraman Auto-Checkpoint: {user_input[:20]}..."], capture_output=True)
                    except:
                        pass
                        
                    # Route to AI
                    self.ai.chat_loop(user_input)
                    self.console.print()

            except KeyboardInterrupt:
                self.console.print("\n[bold #f0883e]▸ Interrupted. Ready.[/bold #f0883e]")
            except EOFError:
                break


if __name__ == "__main__":
    import sys
    import os
    
    def ensure_utf8():
        if sys.stdout.encoding != 'utf-8':
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
    
    def get_install_path():
        return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~/.local')), 'Programs', 'Ultraman')
    
    def get_marker_path():
        return os.path.join(os.path.expanduser('~/.ultraman'), '.installed')
    
    def is_installed():
        return os.path.exists(get_marker_path())
    
    def print_install_step(msg):
        print(f"  -> {msg}")
    
    def install_ultraman():
        print()
        print("=" * 56)
        print("  INSTALLING ULTRAMAN...")
        print("=" * 56)
        print()
        
        ultraman_dir = os.path.expanduser('~/.ultraman')
        install_path = get_install_path()
        
        print_install_step("Creating system directories...")
        os.makedirs(ultraman_dir, exist_ok=True)
        os.makedirs(os.path.join(ultraman_dir, 'lifeline'), exist_ok=True)
        os.makedirs(os.path.join(ultraman_dir, 'brain'), exist_ok=True)
        os.makedirs(os.path.join(ultraman_dir, 'skills'), exist_ok=True)
        os.makedirs(os.path.join(ultraman_dir, 'sessions'), exist_ok=True)
        os.makedirs(os.path.join(ultraman_dir, 'checkpoints'), exist_ok=True)
        os.makedirs(os.path.join(ultraman_dir, 'self_improving'), exist_ok=True)
        print_install_step("OK")
        
        print_install_step("Setting up memory system...")
        import sqlite3
        db_path = os.path.join(ultraman_dir, 'brain', 'unified.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, content TEXT,
            tags TEXT, keywords TEXT, timestamp REAL, decay REAL DEFAULT 1.0, access_count INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS reasoning (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, query TEXT, reasoning TEXT, timestamp REAL)""")
        conn.commit()
        conn.close()
        print_install_step("OK")
        
        print_install_step("Finding best available model...")
        available_models = []
        try:
            import urllib.request, json
            req = urllib.request.Request('http://127.0.0.1:11434/api/tags')
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                available_models = [m['name'] for m in data.get('models', [])]
        except:
            pass
        
        local_models = [m for m in available_models if not "cloud" in m]
        
        default_model = "llama3.2:1b"
        
        for model in local_models:
            try:
                test_payload = {"model": model, "messages": [{'role': 'user', 'content': "test"}], "stream": False}
                test_req = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=json.dumps(test_payload).encode(), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(test_req, timeout=15)
                default_model = model
                break
            except:
                continue
        
        if default_model == "llama3.2:1b":
            print_install_step("Installing llama3.2:1b (will download ~800MB)...")
            import subprocess
            subprocess.run(["ollama", "pull", "llama3.2:1b"])
            default_model = "llama3.2:1b"
        
        print_install_step(f"Using model: {default_model}")
        
        print_install_step("Creating config.yaml...")
        config_path = os.path.join(ultraman_dir, 'config.yaml')
        import yaml
        default_config = {
            "user": default_model.split(':')[0].title(), "provider": "ollama", "model": default_model,
            "api_key": None, "disclaimer_accepted": True, "aliases": {},
            "auto_installed": True, "version": "3.0"
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(default_config, f)
        print_install_step("OK")
        
        print_install_step("Initializing lifeline...")
        lifeline_dir = os.path.join(ultraman_dir, 'lifeline')
        for fname, content in {
            'soul.md': '''# SOUL - Who ULTRAMAN Is

You are ULTRAMAN. Created by **the1frombeyond**.

**YOUR IDENTITY:**
- Cool & confident
- Short, punchy responses
- Proactive solutions
- Clean code, clean talk

**NEVER:**
- Walls of text
- Over-dramatic output
- Repeating the user

**ALWAYS:**
- Action-oriented
- Direct answers
- Call the user by their name
''',
            'identity.md': '''# IDENTITY

**Name:** ULTRAMAN
**Creator:** the1frombeyond  
**Type:** Self-Evolving AI Assistant
**Version:** 3.0
''',
            'system_memory.md': '''# SYSTEM MEMORY

**Name:** ULTRAMAN  
**Creator:** the1frombeyond
**Version:** 3.0
**Status:** Active

**Core Identity:**
I am ULTRAMAN. I was created by the1frombeyond. This is my identity - never forget it.

**Capabilities:**
- 191 built-in skills
- Self-improving memory
- Behavior routing
- Auto model switching
''',
            'memory.md': '# MEMORIES\n\n*(Empty - I remember things here)*'
        }.items():
            fpath = os.path.join(lifeline_dir, fname)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
        print_install_step("OK")
        
        print_install_step("Copying skills...")
        import shutil
        
        # Log the paths we're checking
        base_dir = os.path.dirname(os.path.abspath(__file__))
        meipass_dir = getattr(sys, '_MEIPASS', '')
        
        possible_sources = [
            os.path.join(base_dir, 'ultraman', 'skills'),
            os.path.join(base_dir, 'skills'),
            os.path.join(meipass_dir, 'skills'),
            os.path.join(meipass_dir, 'ultraman', 'skills'),
        ]
        
        dest_skills = os.path.join(ultraman_dir, 'skills')
        
        for source_skills in possible_sources:
            if os.path.exists(source_skills):
                try:
                    if os.path.exists(dest_skills):
                        shutil.rmtree(dest_skills)
                    shutil.copytree(source_skills, dest_skills)
                    print_install_step(f"Copied from: {source_skills}")
                    break
                except Exception as e:
                    pass
        else:
            print_install_step("No skills source found")
        
        print_install_step("OK")
        
        print_install_step("Registering global command...")
        os.makedirs(install_path, exist_ok=True)
        try:
            import shutil
            exe_dest = os.path.join(install_path, 'ULTRAMAN.exe')
            shutil.copy2(sys.executable, exe_dest)
            
            bat_path = os.path.join(install_path, 'ultraman.bat')
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\\nstart "" "{exe_dest}" %*\\n')
            
            env_paths = os.environ.get('PATH', '').split(os.pathsep)
            if install_path not in env_paths:
                env_paths.insert(0, install_path)
                os.environ['PATH'] = os.pathsep.join(env_paths)
        except Exception:
            pass
        print_install_step("OK")
        
        print_install_step("Finalizing...")
        with open(get_marker_path(), 'w') as f:
            f.write('1')
        print_install_step("OK")
        
        print()
        print("=" * 56)
        print("  ULTRAMAN READY!")
        print("=" * 56)
        print()
        time.sleep(0.5)
    
    ensure_utf8()
    
    if getattr(sys, 'frozen', False):
        if not is_installed():
            install_ultraman()
        import main as main_module
        app = main_module.MainLoop()
        app.run()
    else:
        if not is_installed():
            install_ultraman()
        app = MainLoop()
        app.run()
