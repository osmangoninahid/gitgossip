"""A variation of parser functions often needed entire project."""

from datetime import datetime, timedelta


def parse_since(since: str) -> str:
    """Convert a 'since' argument into an ISO date string."""
    since = since.strip().lower()
    if since.endswith("days"):
        try:
            days = int(since.replace("days", "").strip())
        except ValueError:
            raise ValueError(f"{since} is not a valid ISO date")
        return (datetime.now() - timedelta(days=days)).isoformat()
    try:
        dt = datetime.fromisoformat(since)
        return dt.isoformat()
    except ValueError:
        raise ValueError(f"{since} is not a valid ISO date")
