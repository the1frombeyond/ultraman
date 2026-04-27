# ULTRAMAN Feature Summary

## 🎯 CORE FEATURES

### AI & Models
- **Multi-Model Support**: Ollama, OpenAI, Anthropic, OpenRouter
- **Model Switching**: `/switch` command with numbered selection
- **Self-Critique**: Uses secondary model to review responses
- **Deep Reflection**: Think deeply using separate model
- **Auto Model Detection**: Scans available Ollama models

### Memory & Learning
- **Structured Memory Store**: memory_index.py with fast keyword search
- **Memory Types**: Preferences, Goals, Facts, Conversations
- **Memory Decay**: Auto-reduce importance over time
- **Reasoning Layer**: Simple reasoning over memories
- **Personality Learning**: "I like X" → saves to memory.md
- **ST.WALKER**: Log mistakes, create training dataset
- **DR.STRANGE**: Multi-reality simulation
- **BLACK NOIR**: Long-term memory recall & indexing

### Training System (Proponitis)
- **ST.WALKER Training**: Fine-tune on logged mistakes
- **Dataset Management**: Create/import datasets
- **Checkpoint System**: Save/restore model states
- **Experiment Tracking**: Run & track training experiments
- **Model Evaluation**: Performance metrics
- **Export**: Training data, datasets, model cards

### Tools & Skills
| Category | Count | Examples |
|----------|-------|----------|
| Extended Tools | 303 | File ops, git, docker, web |
| Skills | 60+ | remotion, ui-ux-pro-max, web-artifacts |
| MCP Tools | 10+ | read_file, git_status, docker_ps |
| File Creation | 15+ | /pdf, /docx, /xlsx, /html, /py |

### Commands
| Type | Count | Examples |
|------|-------|----------|
| Slash Commands | 50+ | /help, /switch, /newskill |
| Natural Language | 20+ | "create pdf", "switch model" |
| Intent Detection | Auto | No `/` prefix needed |

### UI & Interface
- **Modern Dark Theme**: OpenCode-style colors
- **Rich Terminal UI**: Panels, tables, progress bars
- **Streaming Responses**: Real-time token display
- **Thinking Indicator**: Animated during processing
- **Model Display**: Shows current model in prompt

### MCP Protocol
- **File System Tools**: read, write, list
- **Git Tools**: status, log, commit
- **Docker Tools**: ps, run, build
- **Ollama Tools**: list, pull, manage
- **Shell Commands**: run any command
- **Custom Tools**: Create via MCPCreator

### Portability
- **~/.ultraman/ Structure**: All data portable
- **Core Directories**:
  - `lifeline/` - Identity files
  - `skills/` - Skill modules
  - `brain/` - Brain data
  - `checkpoints/` - Model checkpoints
  - `sessions/` - History
  - `self_improving/` - Learning data

### Automation
- **Brainwaves**: Background task scheduler
- **Cron Support**: Natural language scheduling
- **Skill Stealing**: Import from Claude, Cursor, etc.
- **Auto-import**: Skills from external tools

## 📦 CORE MODULES

| Module | Purpose |
|--------|---------|
| `ai.py` | AI bridge, chat loop, tool calls |
| `memory.py` | Unified memory system |
| `memory_index.py` | Structured memory store |
| `mcp.py` | MCP server & creator |
| `brainwaves.py` | Background automation |
| `st_walker.py` | Self-improvement |
| `dr_strange.py` | Simulation |
| `black_noir.py` | Long-term memory |
| `tools.py` | 303 extended tools |
| `config.py` | Configuration management |
| `vault.py` | Encrypted secrets |

## 🚀 QUICK COMMANDS

```bash
python ultraman.py       # Setup + Launch
python superpowers.py    # Skill management
python proponitis.py     # Training CLI
python mcp.py           # MCP server
```

## 📊 STATS

| Metric | Value |
|--------|-------|
| Extended Tools | 303 |
| Skills | 60+ |
| Commands | 50+ |
| Core Modules | 12 |
| Memory Types | 4 |
| MCP Tools | 10+ |

## ✨ KEY HIGHLIGHTS

1. **No venv needed** - Runs with system Python
2. **Natural language** - No `/` prefix required
3. **Self-evolving** - Learns from mistakes
4. **Portable** - Copy ~/.ultraman to sync
5. **Multi-platform** - Windows, Linux, macOS
6. **Modern UI** - OpenCode-inspired design