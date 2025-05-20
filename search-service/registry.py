import os
from typing import Dict, Any, Optional
from interfaces import SearchStrategy, SearchResult
from handlers import Neo4jHandler, VectorEmbeddingHandler, IndexHandler, OpenAISmartSearchHandler
from search_service import FulltextSearchStrategy, BarcodeSearchStrategy, VectorSearchStrategy, SmartSearchStrategy
from helpers import SuffixStemmerHelper, SearchHelper


class SearchService:
    def __init__(self):
        self._strategies: Dict[str, SearchStrategy] = {}

    def register(self, name: str, strategy: SearchStrategy):
        self._strategies[name] = strategy
        print(f"[SearchService] Registered strategy '{name}'")

    def search(self, strategy_name: str, query: Any, search_level: Optional[str] = None) -> SearchResult:
        if strategy_name not in self._strategies:
            raise ValueError(f"Strategy '{strategy_name}' is not registered.")
        return self._strategies[strategy_name].search(query, search_level=search_level)


search_service = SearchService()

neo4j = Neo4jHandler(
    uri=os.environ.get("NEO4J_URI"),
    username=os.environ.get("NEO4J_USERNAME"),
    password=os.environ.get("NEO4J_PASSWORD")
)
openai_handler = OpenAISmartSearchHandler()
embedding_handler = VectorEmbeddingHandler(neo4j)
index_handler = IndexHandler(neo4j)
stemmer = SuffixStemmerHelper(neo4j)
search_helper = SearchHelper(neo4j, stemmer)
fulltext_strategy = FulltextSearchStrategy(neo4j, index_handler, stemmer, search_helper)
vector_strategy = VectorSearchStrategy(neo4j, embedding_handler, index_handler, search_helper)
smart_strategy = SmartSearchStrategy(neo4j, embedding_handler, search_helper, openai_handler)

search_service.register("fulltext", fulltext_strategy)
search_service.register("barcode", BarcodeSearchStrategy(fulltext_strategy))
search_service.register("vector", vector_strategy)
search_service.register("smart", smart_strategy)

embedding_handler.embed_missing_nodes(label="Waste", text_field="id_normalized")
stemmer.build_suffix_list(label="Waste", field="id_normalized")



