# 🧠 GitGossip — AI-Powered Git Commit Summarizer

**Install via:**  

[![PyPI](https://img.shields.io/pypi/v/gitgossip.svg)](https://pypi.org/project/gitgossip/)
[![Homebrew](https://img.shields.io/badge/homebrew-gitgossip-blue)](https://github.com/osmangoninahid/homebrew-gitgossip)

> **GitGossip** turns your commit history into human-readable summaries and merge request descriptions — powered by LLMs like Ollama (local) or OpenAI (cloud).

GitGossip helps developers and managers instantly understand what changed, why it changed, and how large codebases evolve — **without reading every diff manually**.

---

## 🚀 Features

✅ Generate **smart commit summaries** in natural language  
✅ Produce **Merge Request (MR) titles & descriptions** from code diffs  
✅ AI **commit messages** from staged changes (interactive or git hook)  
✅ Zero-setup mode via **Claude Code or Codex CLI** (no API key, no Ollama)  
✅ **Customizable prompt templates**  
✅ Quickly **list recent commit authors** within a sprint window *(default: 15 days) you may need them to query 😄*  
✅ Works with **local LLMs (Ollama)** *or* **cloud APIs (OpenAI / Anyscale)**  
✅ Fully offline compatible  
✅ Configurable **system resource awareness**  
✅ Clean CLI experience with **Rich formatting**  
✅ Ready for cross-platform use (macOS / Linux)


---

## ⚙️ Installation (macOS / Linux)

### 🧩 Using `uv` (recommended)

```bash
uv tool install gitgossip
````

or clone manually:

```bash
git clone https://github.com/osmangoninahid/gitgossip.git
cd gitgossip
uv sync
uv run gitgossip --help
```

🍺 Using Homebrew

```bash
brew tap osmangoninahid/gitgossip
brew install gitgossip

```

### 🤖 Using your coding agent as the LLM

Already use **Claude Code** or **Codex CLI**? GitGossip can drive them directly — no API key, no Ollama, no model downloads:

```bash
gitgossip init
# → Select LLM provider: agent
# → GitGossip auto-detects installed CLIs (claude / codex)
# → Model override: leave blank for the CLI's default
```

Completions run through your CLI's logged-in account. Slow responses? Raise `llm.timeout` (seconds) in `~/.gitgossip/config.yaml`.

### 🐳 Optional: Run via Docker (Local LLM mode)

If you prefer not to install Ollama on your host:

```bash
docker run -d -p 11434:11434 ollama/ollama
docker exec -it $(docker ps -q -f ancestor=ollama/ollama) ollama pull qwen2.5-coder:1.5b
```

Then configure GitGossip to connect:

```bash
gitgossip init
# → Choose provider: local
# → Base URL: http://localhost:11434/v1
# → Model: qwen2.5-coder:1.5b
```

---

## 🧠 Usage Examples

### 1️⃣ Initialize configuration

```bash
gitgossip init
```

This will interactively ask for:

* LLM provider (`local` or `cloud`)
* Model name (`qwen2.5-coder:1.5b`, `llama3:8b`, etc.)
* API key (if using cloud)
* Auto-detects and warns if your hardware has insufficient memory

Example:

```
Select LLM provider [local/cloud] (local): local
Detected 3 local models from Ollama.
Select or enter model name: qwen2.5-coder:1.5b
⚠️  Warning: Model may require 8 GB RAM. You have 6.2 GB.
Configuration saved successfully!
```

---

### 2️⃣ Summarize commits

```bash
gitgossip summarize --path . --since 7days
```

Example output:

```
╭─────────────────────────────── AI Summary for gitgossip ───────────────────────────────╮
│                                                                                        │
│  - Added local LLM factory and configuration setup                                     │
│  - Integrated interactive CLI initialization                                           │
│  - Improved summarizer to support chunk-based large diff summarization                 │
│                                                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────╯
```

---

### 3️⃣ Generate a Merge Request summary

```bash
gitgossip summarize-mr main
```

Example output:

```
╭────────────────────────────── Merge Request Summary — gitgossip ───────────────────────╮
│                                                                                        │
│  **Refactor and Optimize LLM Integration**                                             │
│                                                                                        │
│  - Added centralized analyzer factory with memory safety checks                        │
│  - Improved configuration for local vs cloud LLMs                                      │
│  - Enhanced CLI UX with color-coded feedback                                           │
│                                                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────╯

✨ Merge Request summary generated successfully!
```

### 4️⃣ List recent commit authors
```bash
gitgossip list-authors
````

By default, this lists all unique authors who have committed within the last 15 days — a typical sprint window.
Authors from the last 15 days
Example output:
```aiignore
1. Osman Goni Nahid <osman@os.ai>
2. Alice Smith <alice@company.com>

Total unique authors: 2

```

Total unique authors: 2

---

You can customize the time window or include all commit history:

```aiignore
# Show authors from the last 30 days
gitgossip list-authors --since 30days

# Show authors from all commits
gitgossip list-authors --all-commits
```

💡 Tip: Use this command to quickly check active contributors before running
gitgossip summarize --author "<name or email>"

### 5️⃣ Generate a commit message

```bash
git add -p
gitgossip commit            # interactive: accept / edit / regenerate / quit
gitgossip commit --print    # just print the message
```

Install as a git hook (fills the message automatically on `git commit`):

```bash
cat > .git/hooks/prepare-commit-msg <<'EOF'
#!/bin/sh
gitgossip commit --hook "$1"
EOF
chmod +x .git/hooks/prepare-commit-msg
```

The hook is fail-open: if the model is unavailable, your commit proceeds untouched.



## ☁️ Local vs Cloud Setup

| Mode      | Description                                                      | Base URL                    | API Key        |
|-----------|------------------------------------------------------------------|-----------------------------|----------------|
| **Local** | Uses [Ollama](https://ollama.ai) or LM Studio for offline models | `http://localhost:11434/v1` | `local`        |
| **Cloud** | Uses OpenAI / Anyscale / Groq APIs                               | `https://api.openai.com/v1` | Required       |
| **Agent** | Uses your installed Claude Code / Codex CLI                      | n/a                         | Uses CLI login |

Your configuration lives at:

```bash
~/.gitgossip/config.yaml
```

Example:

```yaml
llm:
  provider: local          # local | cloud | agent
  agent_cli: ''            # claude | codex (used when provider=agent)
  model: qwen2.5-coder:1.5b
  base_url: http://localhost:11434/v1
  api_key: local
  timeout: 120             # seconds, agent provider only
paths:
  prompts: /Users/osman/.gitgossip/prompts
meta:
  version: '1.0'
```

---

## 🧩 Customize Prompts

GitGossip lets you customize the **LLM prompt templates** behind every command. Scaffold editable copies of the defaults:

```bash
gitgossip prompts init
```

This copies the four templates into your prompts directory (`paths.prompts` in the config, default `~/.gitgossip/prompts/`):

```
~/.gitgossip/prompts/
├── chunk.txt       # per-chunk diff summarization
├── synthesis.txt   # merging chunk summaries
├── final.txt       # MR title + description
└── commit.txt      # commit message generation
```

Edit them freely — user templates always win over the built-in defaults; delete a file to fall back. Available variables: `{{project_name}}`, `{{content}}`, `{{context}}`, `{{metadata}}`.

Use them to define your own tone (technical, business, casual), summary structure (bullets vs prose), or commit-message conventions.

---

## 🧰 Troubleshooting

| Issue                              | Cause                          | Fix                                             |
|------------------------------------|--------------------------------|-------------------------------------------------|
| `OpenAIError: api_key must be set` | API key missing                | Re-run `gitgossip init` or set `api_key: local` |
| `OSError: Connection refused`      | Ollama server not running      | Run `ollama serve` or check Docker port `11434` |
| No models found                    | Ollama empty                   | `ollama pull qwen2.5-coder:1.5b`                |
| Output too short                   | Model truncated due to context | Use smaller `chunk_size` or larger LLM          |
| Slow generation                    | Large diffs or small GPU       | Use cloud LLM for faster inference              |

---

## 🧑‍💻 Contributing

We love community contributions!
Please read the [CONTRIBUTING.md](./CONTRIBUTING.md) guide for:

- Local setup instructions
- Coding standards and pre-commit hooks
- Commit message conventions
- Release and publishing workflow

---

### 🧩 Developer Setup

Clone and install dependencies using [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/osmangoninahid/gitgossip.git
cd gitgossip
make install
```

Once installed, you can use the included Makefile to run all development tasks easily:

| Command                                       | Description                   |
|-----------------------------------------------|-------------------------------|
| `make install`                                | Install all dependencies      |
| `make lint`                                   | Run Ruff linter               |
| `make format`                                 | Format code with Black + Ruff |
| `make test`                                   | Run the full pytest suite     |
| `make run CMD="summarize-mr main --use-mock"` | Run a local CLI command       |
| `make clean`                                  | Clean build/test artifacts    |


---

## 📜 License

MIT License © 2025 [Osman Goni Nahid](https://github.com/osmangoninahid)

