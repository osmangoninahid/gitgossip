# 🧩 Contributing to GitGossip

Thank you for taking the time to contribute!  
This guide explains how to set up your environment, follow our coding standards, and submit high-quality pull requests.

---

## 🧱 Local Setup

1. **Clone the repository**

    ```bash
       git clone https://github.com/osmangoninahid/gitgossip.git
       cd gitgossip
    ````

2. **Install dependencies**

   ```bash
   uv sync --locked
   ```

3. **Install pre-commit hooks**

   ```bash
   uv tool install pre-commit
   pre-commit install --hook-type pre-commit
   pre-commit install --hook-type commit-msg
   ```

4. **Run all checks**

   ```bash
   pre-commit run --all-files
   ```

---

## 🧠 Code Quality Tools

| Tool       | Purpose               |
|------------|-----------------------|
| **Ruff**   | Linting & quick fixes |
| **Black**  | Code formatting       |
| **Isort**  | Import sorting        |
| **Mypy**   | Type checking         |
| **Pylint** | Deep static analysis  |
| **UV**     | Dependency management |

These run automatically via pre-commit.

---

## 🧩 Commit Conventions

GitGossip uses **[Conventional Commits](https://www.conventionalcommits.org/)**.

### Allowed types

```
feat, fix, chore, test, refactor, docs, merge, custom
```

### Examples

```bash
feat(cli): add summarize command
fix(core): handle missing diff lines
docs(readme): update badges
chore(pre-commit): tweak ruff settings
```

> ❗ Non-conforming messages will be blocked by the `commit-msg` hook.

---

## 🧪 Testing

We use **pytest**:

```bash
uv run pytest -v
```

Run all quality checks before pushing:

```bash
make lint
make test
```

---

## 🧰 Common Makefile Commands

| Command                                  | Description                 |
|------------------------------------------|-----------------------------|
| `make install`                           | Install all dependencies    |
| `make lint`                              | Run Ruff linter             |
| `make format`                            | Auto-format code            |
| `make test`                              | Run tests                   |
| `make run CMD="summarize --since 7days"` | Run a CLI command           |
| `make clean`                             | Remove build/test artifacts |

---

## 🚀 Release Workflow (Maintainers)

1. Update code or docs.
2. Bump version in `pyproject.toml` using semantic versioning.
3. Commit with a proper message:

   ```bash
   chore(release): bump version to x.y.z
   ```
4. Tag and push:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
5. GitHub Actions will automatically:

   * Build and publish to **PyPI**
   * Create a **GitHub Release**
   * Update the **Homebrew Formula**

---

## 💬 Getting Help

* Open an [issue](https://github.com/osmangoninahid/gitgossip/issues)
* Discuss ideas in pull-request threads
* Reach out on GitHub Discussions (coming soon)

---

### 🏁 Thank you for helping make GitGossip better!

```