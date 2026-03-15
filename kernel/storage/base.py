from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional


class BaseStorage(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a write query."""
        raise NotImplementedError

    @abstractmethod
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict[str, Any]]:
        """Fetch a single row as a dict."""
        raise NotImplementedError

    @abstractmethod
    def fetch_all(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Fetch multiple rows as dicts."""
        raise NotImplementedError

    @abstractmethod
    def executemany(self, query: str, param_sets: Iterable[tuple]) -> None:
        """Execute a write query against many parameter sets."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the underlying connection."""
        raise NotImplementedError
