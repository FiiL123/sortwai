from abc import ABC, abstractmethod
from typing import Any, TypedDict, Optional


class SearchResult(TypedDict):
    strategy: str
    data: Any


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, query: Any, search_level: Optional[str] = None) -> SearchResult:
        pass
