"""Unit tests for LLMAnalyzer against a fake chat client."""

from gitgossip.core.interfaces.chat_client import IChatClient
from gitgossip.core.llm.errors import ChatClientError
from gitgossip.core.llm.llm_analyzer import LLMAnalyzer
from gitgossip.core.models.commit import Commit


class FakeChatClient(IChatClient):
    """Chat client returning canned output or raising on demand."""

    def __init__(self, reply: str = "canned reply", error: ChatClientError | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[dict] = []

    def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        self.calls.append({"system": system, "user": user, "temperature": temperature, "max_tokens": max_tokens})
        if self.error:
            raise self.error
        return self.reply


def _commit() -> Commit:
    return Commit(
        hash="abc123def456",
        author="osman",
        email="o@x.com",
        message="Fix bug",
        files_changed=1,
        insertions=2,
        deletions=1,
        changes=[],
    )


class TestLLMAnalyzerTransport:
    """Verify LLMAnalyzer delegates to the chat client and maps errors to strings."""

    def test_analyze_commits_uses_chat_client(self) -> None:
        # given
        client = FakeChatClient(reply="nice summary")
        analyzer = LLMAnalyzer(chat_client=client)

        # when
        result = analyzer.analyze_commits([_commit()])

        # then
        assert result == "nice summary"
        assert len(client.calls) == 1
        assert "abc123d" in client.calls[0]["user"]

    def test_analyze_commits_error_returns_llm_error_string(self) -> None:
        # given
        analyzer = LLMAnalyzer(chat_client=FakeChatClient(error=ChatClientError("boom")))

        # when
        result = analyzer.analyze_commits([_commit()])

        # then
        assert result.startswith("[LLM ERROR]")
        assert "boom" in result

    def test_generate_mr_summary_parses_title_and_bullets(self) -> None:
        # given
        client = FakeChatClient(reply="Title: Fix login\nDescription:\n- fix session bug\n- add test")
        analyzer = LLMAnalyzer(chat_client=client)

        # when
        title, description = analyzer.generate_mr_summary("diff --git a/x b/x")

        # then
        assert title == "Fix login"
        assert "- fix session bug" in description

    def test_generate_mr_summary_error_returns_error_tuple(self) -> None:
        # given
        analyzer = LLMAnalyzer(chat_client=FakeChatClient(error=ChatClientError("down")))

        # when
        title, description = analyzer.generate_mr_summary("diff --git a/x b/x")

        # then
        assert title == "[LLM ERROR]"
        assert "down" in description

    def test_summarize_diff_chunk_and_synthesis_delegate(self) -> None:
        # given
        client = FakeChatClient(reply="chunk summary")
        analyzer = LLMAnalyzer(chat_client=client)

        # when
        chunk = analyzer.summarize_diff_chunk("+ new line", metadata="[Part 1/1]")
        synthesis = analyzer.synthesize_chunk_summaries(["a", "b"])

        # then
        assert chunk == "chunk summary"
        assert synthesis == "chunk summary"
        assert len(client.calls) == 2
