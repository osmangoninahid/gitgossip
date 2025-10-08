"""Global constants and parsing rules for GitGossip."""

from __future__ import annotations

import re

# Files that add no semantic value to commit summaries
IGNORED_DIFF_FILES: set[str] = {
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Pipfile.lock",
    "poetry.toml",
    "requirements.txt",
    "Cargo.lock",
}

# File extensions to skip (machine generated or compiled)
IGNORED_EXTENSIONS: set[str] = {
    ".lock",
    ".log",
    ".csv",
    ".min.js",
    ".min.css",
    ".map",
    ".pyc",
    ".pyo",
}

# Max diff size before truncation or skip (in bytes)
MAX_DIFF_SIZE = 50_000

# Potential future config — when we load from .gitgossip.yaml
DEFAULT_CONFIG = {
    "ignore_files": list(IGNORED_DIFF_FILES),
    "ignore_extensions": list(IGNORED_EXTENSIONS),
    "max_diff_size": MAX_DIFF_SIZE,
}

# Function / class detection patterns by language
LANG_FUNC_PATTERNS = {
    "python": re.compile(r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE),
    "go": re.compile(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE),
    "rust": re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE),
    "javascript": re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE),
    "typescript": re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE),
    "java": re.compile(
        r"^\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?[A-Za-z_<>]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        re.MULTILINE,
    ),
}

DEFAULT_FUNC_PATTERN = re.compile(
    r"^\s*(?:def|func|fn|function|class)\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
