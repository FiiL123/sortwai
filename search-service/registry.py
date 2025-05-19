from typing import Dict, Any
from interfaces import SearchStrategy, SearchResult
from handlers import Neo4jHandler
from search_service import FulltextSearchStrategy, BarcodeSearchStrategy


class SearchService:
    def __init__(self):
        self._strategies: Dict[str, SearchStrategy] = {}

    def register(self, name: str, strategy: SearchStrategy):
        self._strategies[name] = strategy
        print(f"[SearchService] Registered strategy '{name}'")

    def search(self, strategy_name: str, query: Any) -> SearchResult:
        if strategy_name not in self._strategies:
            raise ValueError(f"Strategy '{strategy_name}' is not registered.")
        return self._strategies[strategy_name].search(query)


search_service = SearchService()
neo4j = Neo4jHandler(
    uri="bolt://127.0.0.1:7687",
    username="neo4j",
    password="bitnami1"
)
FulltextSearchStrategy(neo4j)
BarcodeSearchStrategy(neo4j)