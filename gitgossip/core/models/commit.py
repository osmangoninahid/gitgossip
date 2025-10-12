"""Commit model definition using Pydantic for structured commit data."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Commit(BaseModel):
    """Represents a Git commit with metadata such as author, date, and stats."""

    hash: str = Field(..., description="The hash of the commit")
    author: str = Field("Unknown author", description="The author of the commit")
    email: str = Field("", description="The email of the commit")
    date: datetime = Field(default_factory=datetime.now)
    message: str | bytes = Field("", description="The commit message")
    insertions: int = Field(0, description="The number of insertions")
    deletions: int = Field(0, description="The number of deletions")
    files_changed: int = Field(0, description="Number of files modified")
    changes: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "example": {
                "hash": "a1b2c3d",
                "author": "Osman Goni Nahid",
                "email": "osman@example.com",
                "date": "2025-10-07T10:00:00Z",
                "message": "fix(bug-x): prevent race conditions",
                "insertions": 42,
                "deletions": 17,
                "files_changed": 3,
            }
        },
    }
