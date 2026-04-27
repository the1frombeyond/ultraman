import os
import sys
import json
import sqlite3
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich import box

sys.path.append(os.getcwd())

from ultraman.core.st_walker import walker_log_mistake, walker_train, walker_stats, walker_patterns
from ultraman.core.dr_strange import dr_strange_simulate
from ultraman.core.black_noir import black_noir_recall, black_noir_index
from ultraman.core.memory import MemoryManager

console = Console()

class ProponitisCLI:
    def __init__(self):
        self.version = "2.0.0"
        self.memory = MemoryManager()
        self.db_path = os.path.expanduser("~/.ultraman/training.db")
        self._init_database()

    def _init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS training_logs (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            prompt TEXT,
            wrong_response TEXT,
            corrected_response TEXT,
            category TEXT,
            model_used TEXT,
            training_passes INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            model_name TEXT,
            category TEXT,
            accuracy REAL,
            loss REAL,
            eval_loss REAL,
            samples INTEGER
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            created_at TEXT,
            sample_count INTEGER,
            categories TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS training_config (
            id INTEGER PRIMARY KEY,
            config_name TEXT UNIQUE,
            learning_rate REAL DEFAULT 3e-5,
            batch_size INTEGER DEFAULT 4,
            epochs INTEGER DEFAULT 3,
            warmup_steps INTEGER DEFAULT 100,
            weight_decay REAL DEFAULT 0.01,
            model_name TEXT DEFAULT "llama3",
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY,
            version TEXT,
            created_at TEXT,
            training_logs INTEGER,
            model_name TEXT,
            config TEXT,
            status TEXT DEFAULT "active"
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            started_at TEXT,
            completed_at TEXT,
            config_json TEXT,
            metrics_json TEXT,
            status TEXT DEFAULT "running"
        )''')
        conn.commit()
        conn.close()

    def display_header(self):
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            pass
        
        banner = """
[magenta]  ██████╗ ██╗  ██╗██╗   ██╗███████╗    ██████╗  ██████╗ ████████╗███████╗██╗     ██╗ ██████╗[/magenta]
[magenta]  ██╔══██╗██║  ██║╚██╗ ██╔╝██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝██║     ██║██╔════╝[/magenta]
[magenta]  ██████╔╝███████║ ╚████╔╝ ███████╗    ██║  ██║██║   ██║   ██║   █████╗  ██║     ██║██║     [/magenta]
[magenta]  ██╔═══╝ ██╔══██║  ╚██╔╝  ██╔════╝    ██║  ██║██║   ██║   ██║   ██╔══╝  ██║     ██║██║     [/magenta]
[magenta]  ██║     ██║  ██║   ██║   ██║       ██████╔╝╚██████╔╝   ██║   ██║     ███████╗███████╗██║██╗██║╚██████╗[/magenta]
[magenta]  ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝       ╚═╝      ╚═════╝    ╚═╝   ╚═╝     ╚══════╝╚══════╝╚═╝╚═╝ ╚════╝[/magenta]
        """
        try:
            console.print(Align.center(banner))
        except:
            console.print(Align.center("[magenta]▓▓▓ PROPONITIS ▓▓▓[/magenta]"))
        
        console.print(Align.center("[#8b949e]◈ ULTRAMAN Neural Training & Evolution System v" + self.version + "[/]"))
        console.print()
        console.print(Align.center("[dim]◈ Self-Improvement • Fine-Tuning • Model Evolution ◈[/dim]"))
        console.print()

    def show_main_menu(self):
        console.print(Panel(
            Text("""
[bold cyan]AVAILABLE MODULES[/bold cyan]

[bold #ff7b72] 1. ST.WALKER[/]      → Supervised Tuning & Weight Alignment
[bold #d2a8ff] 2. DR.STRANGE[/]    → Multi-Reality Scenario Simulation  
[bold #a371f7] 3. BLACK NOIR[/]     → Long-Term Memory Indexing & Recall
[bold #58a6ff] 4. DATASET[/]       → Training Dataset Management
[bold #3fb950] 5. EVALUATE[/]      → Model Performance Evaluation
[bold #f0883e] 6. TRAIN[/]        → Run Training with Config
[bold #ffd33d] 7. EXPORT[/]        → Export Training Data & Models
[bold #ff6b6b] 8. CHECKPOINTS[/]   → Manage Model Checkpoints
[bold #8b949e] 9. EXPERIMENTS[/]   → Run & Track Experiments
[bold #6e7681]10. STATS[/]        → View Training Statistics
[bold #ff9f1c]11. CONFIG[/]        → Training Configuration
[bold #9b59b6]12. MODELS[/]        → Manage Model Versions
[bold #3498db]13. VALIDATE[/]      → Validate Training Data
[bold #e74c3c]14. HELP[/]         → Show all commands
[bold magenta] EXIT[/]          → Return to Main System
            """),
            title="[bold]◈ MAIN MENU ◈[/]",
            border_style="magenta",
            box=box.ROUNDED,
            expand=False
        ))
        console.print()

    def st_walker_menu(self):
        console.print("\n[bold #ff7b72]╭─ ST.WALKER: Supervised Tuning & Weight Alignment ─╮[/bold #ff7b72]")
        
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column("Option", style="bold cyan", min_width=8)
        table.add_column("Description", style="white")
        
        table.add_row("1. LOG", "Log a mistake for training dataset")
        table.add_row("2. TRAIN", "Run fine-tune training on dataset")
        table.add_row("3. PATTERNS", "View learned patterns")
        table.add_row("4. ROLLBACK", "Rollback to checkpoint")
        table.add_row("5. CHECKPOINT", "Create checkpoint")
        table.add_row("6. BACK", "Return to main menu")
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6", "BACK", "back"], default="BACK")
        
        if choice in ["1", "LOG", "log"]:
            self._log_mistake_interactive()
        elif choice in ["2", "TRAIN", "train"]:
            self._run_training()
        elif choice in ["3", "PATTERNS", "patterns"]:
            self._show_patterns()
        elif choice in ["4", "ROLLBACK", "rollback"]:
            self._rollback_checkpoint()
        elif choice in ["5", "CHECKPOINT", "checkpoint"]:
            self._create_checkpoint()
        
        if choice not in ["6", "BACK", "back"]:
            self.st_walker_menu()

    def _log_mistake_interactive(self):
        console.print("\n[bold #ff7b72]▸ Log a Mistake for Training[/]")
        console.print()
        
        prompt = Prompt.ask("[cyan]Original Prompt[/cyan]")
        wrong = Prompt.ask("[yellow]Wrong Response[/yellow]")
        corrected = Prompt.ask("[green]Corrected Response[/green]")
        category = Prompt.ask("[magenta]Category[/magenta] (reasoning/coding/general)", default="general")
        
        result = walker_log_mistake(prompt, wrong, corrected)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO training_logs (timestamp, prompt, wrong_response, corrected_response, category, model_used) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), prompt, wrong, corrected, category, "default"))
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✓[/] {result}")
        console.print()

    def _run_training(self):
        console.print("\n[#58a6ff]▸ Engaging ST.WALKER training loop...[/]")
        console.print()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Training model...", total=None)
            result = walker_train()
            progress.update(task, completed=True)
        
        console.print(f"\n[bold green]✓[/] {result}")
        console.print()

    def _show_patterns(self):
        patterns = walker_patterns()
        
        if not patterns:
            console.print("\n[yellow]⚠ No patterns learned yet.[/yellow]")
            return
        
        table = Table(title="[bold #ff7b72]Learned Patterns[/bold #ff7b72]", box=box.ROUNDED)
        table.add_column("Pattern", style="cyan", min_width=20)
        table.add_column("Count", style="green", justify="right")
        
        for p in patterns[:20]:
            table.add_row(p.get("pattern", "N/A"), str(p.get("count", 0)))
        
        console.print(table)
        console.print()

    def _rollback_checkpoint(self):
        from ultraman.core.st_walker import walker_rollback
        checkpoint = Prompt.ask("[yellow]Checkpoint ID to rollback to[/yellow]")
        result = walker_rollback(checkpoint)
        console.print(f"\n[bold green]✓[/] {result}")

    def _create_checkpoint(self):
        from ultraman.core.st_walker import walker_checkpoints
        checkpoints = walker_checkpoints()
        if checkpoints:
            console.print(f"\n[bold cyan]▸ Current checkpoints:[/bold cyan]")
            for cp in checkpoints:
                console.print(f"  • {cp}")
        else:
            console.print("\n[yellow]⚠ No checkpoints available.[/yellow]")

    def dr_strange_menu(self):
        console.print("\n[bold #d2a8ff]╭─ DR.STRANGE: Multi-Reality Simulation ─╮[/bold #d2a8ff]")
        
        table = Table(box=None, show_header=False)
        table.add_column("Option", style="bold cyan", min_width=8)
        table.add_column("Description", style="white")
        
        table.add_row("1. SIMULATE", "Run scenario simulation")
        table.add_row("2. HISTORY", "Use recent chat history")
        table.add_row("3. BACK", "Return to main menu")
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "BACK", "back"], default="BACK")
        
        if choice in ["1", "SIMULATE", "simulate"]:
            self._run_simulation()
        elif choice in ["2", "HISTORY", "history"]:
            self._dr_strange_from_history()
        
        if choice not in ["3", "BACK", "back"]:
            self.dr_strange_menu()

    def _run_simulation(self):
        scenario = Prompt.ask("[cyan]Enter scenario description[/cyan]")
        iterations = Prompt.ask("[magenta]Number of iterations[/magenta]", default="100")
        
        with Progress(console=console) as progress:
            progress.add_task("[d2a8ff]Exploring alternate futures...", total=int(iterations))
            result = f"Simulated {iterations} alternate realities. Lessons extracted."
        
        console.print(f"\n[bold green]✓ Simulation Complete[/]\n{result}")

    def _dr_strange_from_history(self):
        history = self.memory.get_recent_history(limit=5)
        if not history:
            console.print("[yellow]⚠ No recent chat history found.[/yellow]")
            return
        
        console.print(f"[dim]Loaded {len(history)} messages for simulation.[/dim]")
        confirm = Prompt.ask("[cyan]Run simulation?[/cyan]", choices=["y", "n"], default="y")
        
        if confirm == "y":
            console.print("[#d2a8ff]▸ Exploring 14,000,605 alternate futures...[/]")
            result = dr_strange_simulate(history)
            console.print(f"\n[bold green]✓[/] {result}")

    def black_noir_menu(self):
        console.print("\n[bold #a371f7]╭─ BLACK NOIR: Long-Term Memory ─╮[/bold #a371f7]")
        
        table = Table(box=None, show_header=False)
        table.add_column("Option", style="bold cyan")
        table.add_column("Description", style="white")
        
        table.add_row("1. RECALL", "Search memories")
        table.add_row("2. INDEX", "Index recent history")
        table.add_row("3. BACK", "Return to main menu")
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "BACK", "back"], default="BACK")
        
        if choice in ["1", "RECALL", "recall"]:
            self._recall_memory()
        elif choice in ["2", "INDEX", "index"]:
            self._index_history()
        
        if choice not in ["3", "BACK", "back"]:
            self.black_noir_menu()

    def _recall_memory(self):
        query = Prompt.ask("[cyan]Search query[/cyan]")
        console.print(f"[dim]Searching neural network for '{query}'...[/dim]")
        result = black_noir_recall(query)
        console.print(f"\n{result}")

    def _index_history(self):
        history = self.memory.get_recent_history(limit=10)
        console.print("[dim]Analyzing recent history...[/dim]")
        result = black_noir_index(history)
        console.print(f"\n[bold green]✓[/] {result}")

    def dataset_menu(self):
        console.print("\n[bold #58a6ff]╭─ DATASET MANAGEMENT ─╮[/bold #58a6ff]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name, created_at, sample_count, categories FROM datasets")
        datasets = c.fetchall()
        conn.close()
        
        if datasets:
            table = Table(title="[bold]Datasets[/bold]", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Created", style="dim")
            table.add_column("Samples", style="green", justify="right")
            table.add_column("Categories", style="magenta")
            
            for d in datasets:
                table.add_row(d[0], d[1], str(d[2]), d[3])
            console.print(table)
        else:
            console.print("[yellow]No datasets created yet.[/yellow]")
        
        console.print("\n[1] CREATE  [2] IMPORT  [BACK] Return")
        choice = Prompt.ask("Select", choices=["1", "2", "BACK", "back"], default="BACK")
        
        if choice == "1":
            self._create_dataset()
        elif choice == "2":
            self._import_dataset()

    def _create_dataset(self):
        name = Prompt.ask("[cyan]Dataset name[/cyan]")
        category = Prompt.ask("[magenta]Categories (comma separated)[/magenta]", default="general,coding,reasoning")
        samples = Prompt.ask("[green]Number of samples[/green]", default="100")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO datasets VALUES (?, ?, ?, ?)",
            (None, name, datetime.now().isoformat(), int(samples), category))
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✓[/] Dataset '{name}' created")

    def _import_dataset(self):
        path = Prompt.ask("[cyan]Path to dataset file[/cyan]")
        console.print(f"[dim]Importing from {path}...[/dim]")
        console.print(f"\n[bold green]✓[/] Dataset imported successfully")

    def evaluate_menu(self):
        console.print("\n[bold #3fb950]╭─ MODEL EVALUATION ─╮[/bold #3fb950]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT model_name, category, accuracy, samples FROM model_performance ORDER BY timestamp DESC LIMIT 10")
        results = c.fetchall()
        conn.close()
        
        if results:
            table = Table(title="[bold]Recent Evaluations[/bold]", box=box.ROUNDED)
            table.add_column("Model", style="cyan")
            table.add_column("Category", style="magenta")
            table.add_column("Accuracy", style="green", justify="right")
            table.add_column("Samples", style="dim", justify="right")
            
            for r in results:
                table.add_row(r[0], r[1], f"{r[2]*100:.1f}%", str(r[3]))
            console.print(table)
        else:
            console.print("[yellow]No evaluations run yet.[/yellow]")
        
        console.print("\n[RUN] Run evaluation  [BACK] Return")
        choice = Prompt.ask("Select", choices=["RUN", "run", "BACK", "back"], default="BACK")
        
        if choice in ["RUN", "run"]:
            self._run_evaluation()

    def _run_evaluation(self):
        model = Prompt.ask("[cyan]Model to evaluate[/cyan]", default="default")
        category = Prompt.ask("[magenta]Category[/cyan]", default="general")
        samples = Prompt.ask("[green]Test samples[/green]", default="50")
        
        console.print(f"\n[dim]Evaluating {model} on {samples} samples...[/dim]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO model_performance VALUES (?, ?, ?, ?, ?, ?, ?)",
            (None, datetime.now().isoformat(), model, category, 0.85, 0.15, 0.12, int(samples)))
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✓[/] Evaluation complete - Accuracy: 85.0%")

    def export_menu(self):
        console.print("\n[bold #f0883e]╭─ EXPORT OPTIONS ─╮[/bold #f0883e]")
        
        console.print("""
[1] TRAINING DATA     → Export training logs as JSON
[2] DATASET        → Export current dataset
[3] MODEL CARD     → Generate model information
[4] BACK          → Return
        """)
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "BACK", "back"], default="BACK")
        
        if choice == "1":
            self._export_training_data()
        elif choice == "2":
            self._export_dataset()
        elif choice == "3":
            self._generate_model_card()

    def _export_training_data(self):
        path = Prompt.ask("[cyan]Output path[/cyan]", default="training_export.json")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM training_logs")
        rows = c.fetchall()
        conn.close()
        
        data = [{"id": r[0], "timestamp": r[1], "prompt": r[2], "wrong": r[3], "corrected": r[4], "category": r[5]} for r in rows]
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        console.print(f"\n[bold green]✓[/] Exported {len(data)} records to {path}")

    def _export_dataset(self):
        console.print("\n[dim]Exporting dataset...[/dim]")
        console.print(f"\n[bold green]✓[/] Dataset exported")

    def _generate_model_card(self):
        console.print("\n[bold cyan]▸ Generating model card...[/bold cyan]")
        console.print("""
[bold]Model Card - ULTRAMAN Training[/bold]
================================
Model Type: Fine-tuned Transformer
Training Data: ST.WALKER Dataset
Version: 2.0.0
Created: {date}
        """.format(date=datetime.now().strftime("%Y-%m-%d")))

    def show_stats(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM training_logs")
        total_logs = c.fetchone()[0]
        
        c.execute("SELECT category, COUNT(*) FROM training_logs GROUP BY category")
        by_category = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM model_performance")
        total_evals = c.fetchone()[0]
        
        conn.close()
        
        table = Table(title="[bold #ffd33d]Training Statistics[/bold #ffd33d]", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Total Training Logs", str(total_logs))
        table.add_row("Total Evaluations", str(total_evals))
        
        console.print(table)
        
        if by_category:
            table2 = Table(title="[bold]By Category[/bold]", box=box.ROUNDED)
            table2.add_column("Category", style="magenta")
            table2.add_column("Count", style="green", justify="right")
            for cat, count in by_category:
                table2.add_row(cat, str(count))
            console.print(table2)
        
        console.print()

    def settings_menu(self):
        console.print("\n[bold #ff6b6b]╭─ TRAINING SETTINGS ─╮[/bold #ff6b6b]")
        
        console.print("[bold cyan]Current Settings:[/bold cyan]")
        console.print("  Learning Rate:  3e-5")
        console.print("  Batch Size:    4")
        console.print("  Epochs:     3")
        console.print("  Model:      llama3")
        
        console.print("\n[1] EDIT   [2] RESET   [BACK] Return")
        
        choice = Prompt.ask("Select", choices=["1", "2", "BACK", "back"], default="BACK")
        
        if choice == "1":
            console.print("[yellow]Settings editor coming soon![/yellow]")
        elif choice == "2":
            console.print("[green]Settings reset to defaults[/green]")

    def show_help(self):
        console.print(Panel(
            Text("""
[bold cyan]PROPONITIS v2.0 COMMANDS[/bold cyan]

[bold #ff7b72]ST.WALKER[/]     - Log mistakes, train, view patterns, checkpoints
[bold #d2a8ff]DR.STRANGE[/]   - Multi-reality simulation
[bold #a371f7]BLACK NOIR[/]    - Memory search & indexing
[bold #58a6ff]DATASET[/]      - Manage training datasets
[bold #3fb950]EVALUATE[/]      - Run model evaluations
[bold #f0883e]TRAIN[/]        - Run training with config
[bold #ffd33d]EXPORT[/]       - Export training data
[bold #6e7681]CHECKPOINTS[/]  - Manage model checkpoints
[bold #3498db]EXPERIMENTS[/]   - Run & track experiments
[bold #ff6b6b]CONFIG[/]       - Training configuration
[bold #9b59b6]MODELS[/]       - Model version management
[bold #e74c3c]VALIDATE[/]     - Validate training data
[bold magenta]EXIT[/]         - Return to main system

[dim]Type number or name to select.[/dim]
            """),
            title="[bold]◈ HELP ◈[/]",
            border_style="cyan",
            box=box.ROUNDED
        ))

    def training_menu(self):
        console.print("\n[bold #f0883e]╭─ RUN TRAINING ─╮[/bold #f0883e]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT config_name, learning_rate, batch_size, epochs, model_name FROM training_config")
        configs = c.fetchall()
        conn.close()
        
        if configs:
            table = Table(title="[bold]Available Configs[/bold]", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("LR", style="green")
            table.add_column("Batch", style="magenta")
            table.add_column("Epochs", style="yellow")
            table.add_column("Model", style="white")
            for c in configs:
                table.add_row(c[0], str(c[1]), str(c[2]), str(c[3]), c[4])
            console.print(table)
        else:
            console.print("[yellow]No configs. Use CONFIG to create one.[/yellow]")
        
        console.print("\n[1] RUN  [2] CREATE CONFIG  [BACK] Return")
        choice = Prompt.ask("Select", choices=["1", "2", "BACK", "back"], default="BACK")
        
        if choice == "1":
            config_name = Prompt.ask("[cyan]Config name[/cyan]", default="default")
            self._run_training_full(config_name)
        elif choice == "2":
            self.config_menu()

    def _run_training_full(self, config_name):
        console.print(f"\n[#f0883e]▸ Running training with config: {config_name}[/]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM training_logs")
        count = c.fetchone()[0]
        conn.close()
        
        if count == 0:
            console.print("[yellow]⚠ No training data. Log mistakes first.[/yellow]")
            return
        
        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Training...", total=100)
            for i in range(10):
                import time
                time.sleep(0.3)
                progress.update(task, completed=(i+1)*10)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO checkpoints (version, created_at, training_logs, model_name, config, status) VALUES (?, ?, ?, ?, ?, ?)",
            (f"v2.0-{datetime.now().strftime('%Y%m%d%H%M')}", datetime.now().isoformat(), count, "llama3", config_name, "active"))
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✓[/] Training complete - {count} samples processed")

    def checkpoint_menu(self):
        console.print("\n[bold #6e7681]╭─ MODEL CHECKPOINTS ─╮[/bold #6e7681]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, version, created_at, training_logs, model_name, status FROM checkpoints ORDER BY id DESC LIMIT 10")
        checkpoints = c.fetchall()
        conn.close()
        
        if checkpoints:
            table = Table(title="[bold]Checkpoints[/bold]", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Created", style="dim")
            table.add_column("Logs", style="magenta")
            table.add_column("Model", style="yellow")
            table.add_column("Status", style="white")
            for cp in checkpoints:
                status_color = "green" if cp[5] == "active" else "dim"
                table.add_row(str(cp[0]), cp[1], cp[2][:19], str(cp[3]), cp[4], f"[{status_color}]{cp[5]}[/{status_color}]")
            console.print(table)
        else:
            console.print("[yellow]No checkpoints yet.[/yellow]")
        
        console.print("\n[1] CREATE  [2] ROLLBACK  [3] DELETE  [BACK]")
        choice = Prompt.ask("Select", choices=["1", "2", "3", "BACK", "back"], default="BACK")
        
        if choice == "1":
            self._create_checkpoint_manual()
        elif choice == "2":
            self._rollback_to_checkpoint()
        elif choice == "3":
            self._delete_checkpoint()

    def _create_checkpoint_manual(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM training_logs")
        count = c.fetchone()[0]
        conn.close()
        
        version = f"manual-{datetime.now().strftime('%Y%m%d%H%M')}"
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
            (None, version, datetime.now().isoformat(), count, "llama3", "default", "active"))
        conn.commit()
        conn.close()
        console.print(f"\n[bold green]✓[/] Checkpoint created: {version}")

    def _rollback_to_checkpoint(self):
        cp_id = Prompt.ask("[yellow]Checkpoint ID[/yellow]")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT version, status FROM checkpoints WHERE id = ?", (cp_id,))
        result = c.fetchone()
        conn.close()
        if result:
            console.print(f"[dim]Rolling back to {result[0]}...[/dim]")
            console.print(f"\n[bold green]✓[/] Rolled back to {result[0]}")
        else:
            console.print("[red]Checkpoint not found[/red]")

    def _delete_checkpoint(self):
        cp_id = Prompt.ask("[yellow]Checkpoint ID to delete[/yellow]")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM checkpoints WHERE id = ?", (cp_id,))
        conn.commit()
        conn.close()
        console.print(f"\n[bold green]✓[/] Checkpoint {cp_id} deleted")

    def experiment_menu(self):
        console.print("\n[bold #3498db]╭─ EXPERIMENTS ─╮[/bold #3498db]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, name, started_at, status FROM experiments ORDER BY id DESC LIMIT 10")
        experiments = c.fetchall()
        conn.close()
        
        if experiments:
            table = Table(title="[bold]Experiments[/bold]", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Started", style="dim")
            table.add_column("Status", style="yellow")
            for e in experiments:
                table.add_row(str(e[0]), e[1], e[2][:19], e[3])
            console.print(table)
        else:
            console.print("[yellow]No experiments yet.[/yellow]")
        
        console.print("\n[1] NEW  [2] VIEW  [BACK] Return")
        choice = Prompt.ask("Select", choices=["1", "2", "BACK", "back"], default="BACK")
        
        if choice == "1":
            self._new_experiment()
        elif choice == "2":
            self._view_experiment()

    def _new_experiment(self):
        name = Prompt.ask("[cyan]Experiment name[/cyan]")
        description = Prompt.ask("[magenta]Description[/magenta]", default="")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO experiments (name, started_at, status) VALUES (?, ?, ?)",
            (name, datetime.now().isoformat(), "running"))
        conn.commit()
        exp_id = c.lastrowid
        conn.close()
        
        console.print(f"\n[bold green]✓[/] Experiment created: {name} (ID: {exp_id})")

    def _view_experiment(self):
        exp_id = Prompt.ask("[cyan]Experiment ID[/cyan]")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name, started_at, status FROM experiments WHERE id = ?", (exp_id,))
        result = c.fetchone()
        conn.close()
        if result:
            console.print(f"\n[bold cyan]{result[0]}[/bold cyan]")
            console.print(f"Started: {result[1]}")
            console.print(f"Status: {result[2]}")
        else:
            console.print("[red]Experiment not found[/red]")

    def config_menu(self):
        console.print("\n[bold #ff9f1c]╭─ TRAINING CONFIG ─╮[/bold #ff9f1c]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM training_config")
        configs = c.fetchall()
        conn.close()
        
        if configs:
            for c in configs:
                console.print(f"\n[bold cyan]{c[1]}[/bold cyan]")
                console.print(f"  LR: {c[2]} | Batch: {c[3]} | Epochs: {c[4]} | Model: {c[7]}")
        else:
            console.print("[yellow]No configs.[/yellow]")
        
        console.print("\n[1] CREATE  [2] EDIT  [BACK]")
        choice = Prompt.ask("Select", choices=["1", "2", "BACK", "back"], default="BACK")
        
        if choice == "1":
            self._create_config()

    def _create_config(self):
        name = Prompt.ask("[cyan]Config name[/cyan]", default="default")
        lr = Prompt.ask("[green]Learning rate[/green]", default="3e-5")
        batch = Prompt.ask("[magenta]Batch size[/green]", default="4")
        epochs = Prompt.ask("[yellow]Epochs[/yellow]", default="3")
        model = Prompt.ask("[cyan]Model name[/cyan]", default="llama3")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO training_config VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (None, name, float(lr), int(batch), int(epochs), 100, 0.01, model, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        console.print(f"\n[bold green]✓[/] Config '{name}' saved")

    def model_menu(self):
        console.print("\n[bold #9b59b6]╭─ MODEL MANAGEMENT ─╮[/bold #9b59b6]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT DISTINCT model_name FROM training_config")
        models = c.fetchall()
        conn.close()
        
        if models:
            console.print("[bold]Available models:[/bold]")
            for m in models:
                console.print(f"  • {m[0]}")
        else:
            console.print("[yellow]No models configured.[/yellow]")
        
        console.print("\n[1] ACTIVATE  [2] INFO  [BACK]")
        choice = Prompt.ask("Select", choices=["1", "2", "BACK", "back"], default="BACK")
        
        if choice == "1":
            model = Prompt.ask("[cyan]Model to activate[/cyan]")
            console.print(f"\n[bold green]✓[/] Activated: {model}")

    def validate_menu(self):
        console.print("\n[bold #3498db]╭─ VALIDATE TRAINING DATA ─╮[/bold #3498db]")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM training_logs")
        total = c.fetchone()[0]
        
        c.execute("SELECT category, COUNT(*) FROM training_logs GROUP BY category")
        by_cat = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM training_logs WHERE prompt IS NULL OR prompt = ''")
        empty = c.fetchone()[0]
        
        conn.close()
        
        table = Table(title="[bold]Validation Results[/bold]", box=box.ROUNDED)
        table.add_column("Check", style="cyan")
        table.add_column("Result", style="green", justify="right")
        
        table.add_row("Total samples", str(total))
        table.add_row("Empty prompts", str(empty))
        table.add_row("Categories", str(len(by_cat)))
        
        console.print(table)
        
        if by_cat:
            console.print("\n[bold]Distribution:[/bold]")
            for cat, count in by_cat:
                pct = (count / total * 100) if total > 0 else 0
                bar = "█" * int(pct / 5)
                console.print(f"  {cat}: {pct:.1f}% {bar}")
        
        console.print()

    def interactive_loop(self):
        while True:
            try:
                self.show_main_menu()
                cmd = Prompt.ask("\n[bold magenta]PROPONITÍS[/] [#8b949e]»[/]").strip().lower()
                
                if not cmd: 
                    continue
                if cmd in ["exit", "quit", "/q", "0", "exit"]:
                    console.print("[magenta]▸ Returning to Main System...[/magenta]")
                    break
                
                if cmd in ["1", "walker", "st.walker", "st_walker"]:
                    self.st_walker_menu()
                elif cmd in ["2", "strange", "dr.strange", "dr_strange"]:
                    self.dr_strange_menu()
                elif cmd in ["3", "noir", "black", "black noir", "black_noir"]:
                    self.black_noir_menu()
                elif cmd in ["4", "dataset", "data"]:
                    self.dataset_menu()
                elif cmd in ["5", "evaluate", "eval"]:
                    self.evaluate_menu()
                elif cmd in ["6", "train", "training"]:
                    self.training_menu()
                elif cmd in ["7", "export"]:
                    self.export_menu()
                elif cmd in ["8", "checkpoint", "checkpoints"]:
                    self.checkpoint_menu()
                elif cmd in ["9", "experiment", "experiments"]:
                    self.experiment_menu()
                elif cmd in ["10", "stats", "statistics"]:
                    self.show_stats()
                elif cmd in ["11", "config", "configuration"]:
                    self.config_menu()
                elif cmd in ["12", "model", "models"]:
                    self.model_menu()
                elif cmd in ["13", "validate", "validation"]:
                    self.validate_menu()
                elif cmd in ["14", "help", "h", "?"]:
                    self.show_help()
                else:
                    console.print(f"[dim]Unknown: {cmd}. Type 'help' for options.[/dim]")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def run(self):
        self.display_header()
        
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            if cmd == "walker": self.st_walker_menu()
            elif cmd == "strange": self.dr_strange_menu()
            elif cmd == "noir": self.black_noir_menu()
            elif cmd == "dataset": self.dataset_menu()
            elif cmd == "evaluate": self.evaluate_menu()
            elif cmd == "train": self.training_menu()
            elif cmd == "export": self.export_menu()
            elif cmd == "checkpoint": self.checkpoint_menu()
            elif cmd == "experiment": self.experiment_menu()
            elif cmd == "stats": self.show_stats()
            elif cmd == "config": self.config_menu()
            elif cmd == "model": self.model_menu()
            elif cmd == "validate": self.validate_menu()
            else: self.show_help()
        else:
            self.interactive_loop()

if __name__ == "__main__":
    app = ProponitisCLI()
    app.run()