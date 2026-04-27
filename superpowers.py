import os
import sys
import json
import sqlite3
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt

# Ensure parent directory is in path for imports
sys.path.append(os.getcwd())

from ultraman.core.memory import MemoryManager
from ultraman.ui.branding import OPENCODE_COLORS, UltramanUI

console = Console()

class SuperpowersCLI:
    def __init__(self):
        self.memory = MemoryManager()
        self.version = "1.0.0"

    def display_header(self):
        # Clear console
        os.system('cls' if os.name == 'nt' else 'clear')
        
        banner = """
[red] █▀▀█ █  █ █▀▀█ █▀▀█ █▀▀█ █▀▀█ █▀▀█ █   █ █▀▀█ █▀▀█ █▀▀█ [/red]
[red] ▀▀▄▄ █  █ █▄▄█ █▀▀  █▄▄▀ █▄▄█ █  █ █▄█▄█ █▀▀  █▄▄▀ ▀▀▄▄ [/red]
[red] █▄▄█ ▀▄▄▀ █    ▀▀▀▀ █ ▀▄ █    █▄▄█  ▀ ▀  ▀▀▀▀ █ ▀▄ █▄▄█ [/red]
        """
        try:
            console.print(Align.center(banner))
        except UnicodeEncodeError:
            console.print(Align.center("[red]ULTRAMAN[/red]"))
            
        console.print(Align.center("[#8b949e]ULTRAMAN Skill Database System v" + self.version + "[/]"))
        console.print()

    def list_skills(self):
        skills = self.memory.get_skills()
        if not skills:
            console.print("[yellow]⚠ No skills registered in the database. Use 'sync' to index files.[/]")
            return

        table = Table(title="[bold #58a6ff]Registered Superpowers[/]", border_style="#30363d", expand=True)
        table.add_column("Name", style="bold #58a6ff", width=20)
        table.add_column("Category", style="#a371f7", width=15)
        table.add_column("Description", style="#c9d1d9")
        table.add_column("Created", style="dim", width=20)

        for s in skills:
            table.add_row(s['name'], s['category'] or "General", s['desc'] or "No description", s['created'])

        console.print(table)

    def search(self, query):
        results = self.memory.search_skills(query)
        if not results:
            console.print(f"[red]✕ No superpowers found matching:[/red] '{query}'")
            return

        table = Table(title=f"[bold #ffc107]Search Results for '{query}'[/]", border_style="#30363d", expand=True)
        table.add_column("Name", style="bold #58a6ff")
        table.add_column("Category", style="#a371f7")
        table.add_column("Description", style="#c9d1d9")

        for s in results:
            table.add_row(s['name'], s['category'] or "General", s['desc'] or "No description")

        console.print(table)

    def sync_filesystem(self):
        """Scan directories and sync with database"""
        console.print("[#58a6ff]▸ Synchronizing filesystem skills...[/]")
        
        # Use script-relative path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dirs_to_scan = [
            os.path.join(script_dir, "ultraman", "skills"),
        ]
        
        count = 0
        for sdir in dirs_to_scan:
            if not os.path.exists(sdir): continue
            
            for root, dirs, files in os.walk(sdir):
                for f in files:
                    if f.endswith(".md") or f.endswith(".py"):
                        path = os.path.join(root, f)
                        name = os.path.splitext(f)[0]
                        
                        # Trivial metadata extraction
                        desc = "Automated skill"
                        category = "System"
                        if f.endswith(".md"):
                            try:
                                with open(path, "r", encoding="utf-8") as file:
                                    content = file.read(500)
                                    if "description:" in content.lower():
                                        # Simple extraction
                                        import re
                                        m = re.search(r"description:\s*(.*)", content, re.IGNORECASE)
                                        if m: desc = m.group(1).strip()
                            except: pass
                        
                        self.memory.register_skill(name, desc, category, path)
                        count += 1
        
        console.print(f"[bold #3fb950]✓ Synchronized {count} skills with the database.[/bold #3fb950]")

    def show_info(self, skill_name):
        results = self.memory.search_skills(skill_name)
        if not results:
            console.print(f"[red]✕ Skill not found:[/red] '{skill_name}'")
            return
            
        skill = results[0]
        console.print(f"\n[bold #58a6ff]╭─ SKILL: {skill['name']} ──────────────────────────────╮[/]")
        console.print(f"│ Category: {skill.get('category') or 'General'}")
        console.print(f"│ Path:     {skill.get('path', 'Unknown')}")
        console.print(f"│ Created:  {skill.get('created', 'Unknown')}")
        console.print(f"[bold #58a6ff]╰────────────────────────────────────────────────────╯[/]\n")
        
        path = skill.get('path')
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Show first 30 lines
                lines = content.split('\n')
                preview = '\n'.join(lines[:30])
                if len(lines) > 30:
                    preview += "\n... [dim](content truncated)[/dim]"
                
                from rich.markdown import Markdown
                from rich.syntax import Syntax
                if path.endswith(".md"):
                    console.print(Markdown(preview))
                else:
                    console.print(Syntax(preview, "python", theme="monokai", line_numbers=True))
            except Exception as e:
                console.print(f"[red]Could not read file: {e}[/red]")

    def create_skill(self, skill_name):
        from ultraman.core.config import ULTRAMAN_SKILLS_DIR
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_dir_proj = os.path.join(script_dir, "ultraman", "skills", skill_name)
        skill_dir_user = os.path.join(ULTRAMAN_SKILLS_DIR, skill_name)
        
        if os.path.exists(skill_dir_proj) or os.path.exists(skill_dir_user):
            console.print(f"[yellow]⚠ Skill directory '{skill_name}' already exists.[/]")
            return
            
        os.makedirs(skill_dir_proj, exist_ok=True)
        os.makedirs(skill_dir_user, exist_ok=True)
        md_path_proj = os.path.join(skill_dir_proj, "SKILL.md")
        md_path_user = os.path.join(skill_dir_user, "SKILL.md")
        
        console.print(f"[#58a6ff]▸ Engaging AI to synthesize '{skill_name}' skill...[/]")
        template = ""
        try:
            from ultraman.core.ai import AIBridge
            ai = AIBridge()
            prompt = f"Create a comprehensive markdown SKILL.md file for a new AI agent skill called '{skill_name}'. Include frontmatter with name, description, category. Include sections for Description, Triggers, and Instructions. Output ONLY raw markdown without code blocks."
            result = ai.generate_skill_code(prompt)
            if result and not result.startswith("# Error"):
                template = result
        except Exception as e:
            console.print(f"[yellow]⚠ AI generation failed ({e}). Falling back to manual template.[/]")
            
        if not template:
            template = f"""---
name: {skill_name}
description: A new superpower skill for ULTRAMAN.
category: Custom
---

# {skill_name.replace('-', ' ').title()}

## Description
Provide a detailed description of what this skill does and when to use it.

## Triggers
- "use {skill_name.replace('-', ' ')}"
- "trigger custom skill"

## Instructions
1. Step one
2. Step two
"""
        # Clean up any AI markdown wrapping if it leaked
        if template.startswith("```markdown"): template = template[11:]
        if template.endswith("```"): template = template[:-3]
        template = template.strip()

        with open(md_path_proj, "w", encoding="utf-8") as f:
            f.write(template)
        with open(md_path_user, "w", encoding="utf-8") as f:
            f.write(template)
            
        console.print(f"[bold #3fb950]✓ Skill scaffolded at:[/bold #3fb950] {skill_dir_proj}")
        console.print(f"[dim]└ Also saved to:[/dim] {skill_dir_user}")
        self.sync_filesystem()

    def steal_skills(self, source):
        """Steal skills from other AI CLIs like Antigravity, OpenCode, Claude"""
        import shutil
        console.print(f"[#58a6ff]▸ Attempting to infiltrate '{source}' skill repository...[/]")
        
        home = os.path.expanduser("~")
        sources = {
            "antigravity": os.path.join(home, ".gemini", "antigravity", "skills"),
            "opencode": os.path.join(home, "opencode", "skills"),
            "claude": os.path.join(home, ".claude", "skills"),
            "cline": os.path.join(home, ".cline", "skills")
        }
        
        target_src = sources.get(source.lower())
        if not target_src:
            target_src = source  # Assume they provided a raw path
            
        if not os.path.exists(target_src):
            console.print(f"[red]✕ Target repository not found at: {target_src}[/]")
            return
            
        dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ultraman", "skills")
        os.makedirs(dest_dir, exist_ok=True)
        
        # Check for existing skills first
        existing_skills = set()
        for root, dirs, files in os.walk(dest_dir):
            for f in files:
                if f.endswith(".md") or f.endswith(".py"):
                    existing_skills.add(f)
        
        to_copy = []
        skip_count = 0
        
        console.print(f"[dim]Scanning {target_src}...[/dim]")
        for root, dirs, files in os.walk(target_src):
            for f in files:
                if f.endswith(".md") or f.endswith(".py"):
                    src_path = os.path.join(root, f)
                    parent_name = os.path.basename(root)
                    if parent_name == "skills":
                        dst_path = os.path.join(dest_dir, f)
                    else:
                        nested_dest = os.path.join(dest_dir, parent_name)
                        os.makedirs(nested_dest, exist_ok=True)
                        dst_path = os.path.join(nested_dest, f)
                    
                    if os.path.exists(dst_path):
                        skip_count += 1
                        to_copy.append((src_path, dst_path, f, True))  # True = exists
                    else:
                        to_copy.append((src_path, dst_path, f, False))  # False = new
        
        # If there are existing skills, ask for confirmation
        existing_to_replace = [x for x in to_copy if x[3]]
        if existing_to_replace:
            console.print(f"\n[yellow]⚠ Found {len(existing_to_replace)} skills already exist:[/yellow]")
            for _, _, f, _ in existing_to_replace[:5]:
                console.print(f"  • {f}")
            if len(existing_to_replace) > 5:
                console.print(f"  ... and {len(existing_to_replace) - 5} more")
            
            confirm = Prompt.ask(
                f"\n[bold #f0883e]Replace {len(existing_to_replace)} existing skills?[/bold #f0883e]",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() != "y":
                console.print(f"\n[{OPENCODE_COLORS['dim']}]▸ Import cancelled.[/{OPENCODE_COLORS['dim']}]")
                return
            
            # Filter out existing ones that user chose not to replace
            to_copy = [x for x in to_copy if not x[3]]
        
        count = 0
        for src_path, dst_path, f, _ in to_copy:
            shutil.copy2(src_path, dst_path)
            count += 1
            console.print(f"  [dim]+ Stole: {f}[/dim]")

        if count > 0:
            console.print(f"[bold #3fb950]✓ Successfully assimilated {count} new skills from {source}![/bold #3fb950]")
            self.sync_filesystem()
        else:
            if skip_count > 0:
                console.print(f"[dim]▸ No new skills to steal. {skip_count} already existed.[/dim]")
            else:
                console.print(f"[yellow]⚠ Found no skills to steal from {source}.[/yellow]")

    def show_stats(self):
        skills = self.memory.get_skills()
        if not skills:
            console.print("[yellow]⚠ No skills registered.[/]")
            return
            
        total = len(skills)
        categories = {}
        for s in skills:
            cat = s.get('category') or 'General'
            categories[cat] = categories.get(cat, 0) + 1
            
        console.print("\n[bold #a371f7]Superpowers Statistics[/]")
        console.print(f"Total Skills: [bold #58a6ff]{total}[/]")
        
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column("Category", style="#c9d1d9")
        table.add_column("Count", style="bold #3fb950")
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            table.add_row(f"• {cat}", str(count))
            
        console.print(Panel(table, title="By Category", border_style="#30363d", expand=False))

    def run(self):
        self.display_header()
        
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            if cmd == "list":
                self.list_skills()
            elif cmd == "search" and len(sys.argv) > 2:
                self.search(" ".join(sys.argv[2:]))
            elif cmd == "info" and len(sys.argv) > 2:
                self.show_info(sys.argv[2])
            elif cmd == "create" and len(sys.argv) > 2:
                self.create_skill(sys.argv[2])
            elif cmd == "steal" and len(sys.argv) > 2:
                self.steal_skills(sys.argv[2])
            elif cmd == "stats":
                self.show_stats()
            elif cmd == "sync":
                self.sync_filesystem()
            else:
                self.show_help()
        else:
            self.interactive_loop()

    def show_help(self):
        console.print("[bold]Usage:[/bold] python superpowers.py [command] [args]")
        console.print("\n[bold]Commands:[/bold]")
        console.print("  list         - List all registered skills")
        console.print("  search <q>   - Search skills by keyword")
        console.print("  info <name>  - Show details and code/markdown for a skill")
        console.print("  create <name>- Use AI to scaffold a new skill automatically")
        console.print("  steal <src>  - Steal skills from 'antigravity', 'opencode', etc.")
        console.print("  stats        - Show database statistics")
        console.print("  sync         - Sync filesystem with database")
        console.print("  exit         - Return to ULTRAMAN")
        console.print("  help         - Show this help message")

    def interactive_loop(self):
        while True:
            try:
                cmd = Prompt.ask("\n[bold #58a6ff]SUPERPOWERS[/] [#8b949e]»[/]").strip().lower()
                if not cmd: continue
                if cmd in ["exit", "quit", "/q"]: 
                    console.print("[#58a6ff]▸ Returning to ULTRAMAN...[/]")
                    break
                
                parts = cmd.split()
                action = parts[0]
                
                if action == "list":
                    self.list_skills()
                elif action == "search" and len(parts) > 1:
                    self.search(" ".join(parts[1:]))
                elif action == "info" and len(parts) > 1:
                    self.show_info(parts[1])
                elif action == "create" and len(parts) > 1:
                    self.create_skill(parts[1])
                elif action == "steal" and len(parts) > 1:
                    self.steal_skills(parts[1])
                elif action == "stats":
                    self.show_stats()
                elif action == "sync":
                    self.sync_filesystem()
                elif action == "help":
                    self.show_help()
                else:
                    console.print(f"[dim]Unknown command: {action}. Type 'help' for options.[/dim]")
            except KeyboardInterrupt:
                break
        console.print("\n[dim]Disconnected from Superpowers database.[/dim]")

if __name__ == "__main__":
    app = SuperpowersCLI()
    app.run()
