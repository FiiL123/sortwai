from abc import ABC, abstractmethod
from typing import Any, TypedDict


class SearchResult(TypedDict):
    strategy: str
    data: Any


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, query: Any) -> SearchResult:
        pass
