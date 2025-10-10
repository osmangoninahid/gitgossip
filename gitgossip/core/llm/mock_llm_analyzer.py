"""Mock implementation of ILLMAnalyzer for local testing and simulation."""

from __future__ import annotations

from gitgossip.core.interfaces.llm_analyzer import ILLMAnalyzer
from gitgossip.core.models.commit import Commit


class MockLLMAnalyzer(ILLMAnalyzer):
    """Simulates LLM commit analysis for development and unit testing."""

    def __init__(self, verbosity: int = 1) -> None:
        """Initialize the mock analyzer."""
        self.__verbosity = verbosity

    def analyze_commits(self, commits: list[Commit]) -> str:
        """Generate human-readable summaries of commits without real LLM."""
        if not commits:
            return "No commits found to analyze."

        output: list[str] = []
        for commit in commits:
            hash_ = commit.hash[:7]
            author = commit.author
            message = (
                commit.message.decode("utf-8", "ignore") if isinstance(commit.message, bytes) else str(commit.message)
            )
            files = commit.files_changed
            insertions = commit.insertions
            deletions = commit.deletions

            summary = f"Commit `{hash_}` by {author}: {message} (+{insertions}/-{deletions}, {files} files)."

            if self.__verbosity > 1 and commit.changes:
                summary += "\n  Highlights:"
                for ch in commit.changes[:2]:
                    summary += f"\n   - {ch['file']}: {'; '.join(ch.get('summary', [])[:2])}"

            output.append(summary)

        return "\n\n".join(output)

    def generate_mr_summary(self, diff_text: str) -> tuple[str, str]:
        """Simulate Merge Request title and description generation from a diff."""
        if not diff_text or not diff_text.strip():
            return "No changes detected", "No differences found between branches."

        # Build a simple fake MR summary
        total_lines = len(diff_text.splitlines())
        changed_files = sum(1 for line in diff_text.splitlines() if line.startswith("diff --git"))

        title = f"Mock MR Summary for {changed_files} files changed"
        description_lines = [
            f"- Total diff lines analyzed: {total_lines}",
            f"- Files impacted: {changed_files}",
            "- Simulated code changes detected successfully.",
            "- (This is a mock summary; no real LLM used.)",
        ]

        return title, "\n".join(description_lines)
