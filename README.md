# ULTRAMAN

**Your Personal AI Assistant That Remembers You**

---

## What is ULTRAMAN?

ULTRAMAN is a self-evolving AI assistant that:

- Remembers your preferences and context
- Helps you build anything
- Learns from your interactions
- Works entirely offline with local AI models

> *"I don't just answer questions - I remember you and get better over time."*

---

## Quick Start

### Install (30 seconds)

```bash
python install.py
```
also download the ultraman.exe file

### Run

```bash
ultraman
```

That's it. No configuration needed.

---

## Features

### Memory That Lasts
ULTRAMAN remembers your preferences, your projects, and your context across sessions.

### Self-Improving
Tell ULTRAMAN when it gets something wrong, and it learns. Each correction makes it better.

### 180+ Built-in Tools
File operations, code execution, web search, Docker management, database tools, and more.

### Privacy First
Your data stays on your machine. No cloud, no external servers.

### Behavior Routing
ULTRAMAN analyzes what you're asking and routes to the right mode - fast responses, deep reasoning, or creative exploration.

---

## Requirements

- Python 3.10+
- Ollama (for local AI models)

### Recommended: Ollama

For the best experience, install Ollama:

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

Then pull a model:

```bash
ollama pull llama3.1
```

---

## Installation Options

### Option 1: Quick Install (Recommended)

```bash
git clone https://github.com/the1frombeyond/ultraman.git
cd ultraman
python install.py
```

### Option 2: Executable

Download `ULTRAMAN.exe` from releases and double-click to install.

---

## Usage

### Basic Chat

```bash
ultraman
> You: Help me write a Python script
```

### Pass Arguments Directly

```bash
ultraman "What files changed today?"
```

### Learn from Feedback

```bash
> ULTRAMAN: Here's the code...
> You: That approach is wrong because...
```

ULTRAMAN logs this and improves.

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/skills` | List available skills |
| `/memory` | View memory stats |
| `/brain` | Switch AI model |
| `/exit` | Exit ULTRAMAN |

---

## Directory Structure

All data is stored in `~/.ultraman/`:

```
~/.ultraman/
├── lifeline/       # Personality & identity
├── brain/         # Memory database
├── skills/        # Skill modules
├── sessions/      # Conversation history
└── config.yaml   # Your configuration
```

---

## Troubleshooting

### "Ollama not running"
```bash
ollama serve
```

### "Model not found"
```bash
ollama pull llama3.1
```

### Need help?
Open an issue on GitHub.

---

## License

MIT License

---

**Built by the1frombeyond | H.A.I.L. MARY Project**

*"The future is personal AI that respects your privacy."*
