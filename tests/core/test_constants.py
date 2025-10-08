"""Unit tests for constants."""

from gitgossip.core.constants import LANG_FUNC_PATTERNS


def test_func_patterns_cover_common_languages() -> None:
    """Tests language classes/functions pattern."""
    # given
    samples = {
        "python": "def foo(): pass",
        "go": "func ServeHTTP() {}",
        "rust": "fn compute() {}",
        "javascript": "function doThing() {}",
        "java": "public static void main(String[] args) {}",
    }
    # when
    for lang, code in samples.items():
        pattern = LANG_FUNC_PATTERNS[lang]

        # then
        assert pattern.search(code), f"Pattern failed for {lang}"
