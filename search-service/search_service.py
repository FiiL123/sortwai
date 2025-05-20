from typing import List, Dict, Any, Optional
from interfaces import SearchStrategy, SearchResult
from handlers import Neo4jHandler, VectorEmbeddingHandler, IndexHandler, OpenAISmartSearchHandler
from helpers import SuffixStemmerHelper, SearchHelper


class FulltextSearchStrategy(SearchStrategy):
    def __init__(self, neo4j_handler: Neo4jHandler, index_handler: IndexHandler,
                 stemmer: SuffixStemmerHelper, search_helper: SearchHelper):
        self.neo4j = neo4j_handler
        self.index_handler = index_handler
        self.stemmer = stemmer
        self.search_helper = search_helper
        self.index_name = "fulltext_id_normalized_index"
        self.parameter = "id_normalized"
        index_handler.ensure_fulltext_index(self.index_name, ["Category", "Waste", "Bin"], "id_normalized")

    def search(self, query: Any, search_level: str = "waste") -> SearchResult:
        if not isinstance(query, list) or not all(isinstance(word, str) for word in query):
            raise ValueError("FulltextSearchStrategy expects a list of strings as input.")

        result_map: Dict[str, Dict[str, List[str]]] = {}
        for keyword in query:
            category_ids = []
            all_bins = []

            if search_level == "waste":
                results = self.search_helper.get_waste_from_keyword(keyword, self.index_name, "1", "fulltext")
                if not results:
                    result_map[keyword] = {"Categories": [], "Bins": []}
                    continue
                top_waste_id = results[0]["waste_id"]
                if top_waste_id:
                    category_ids = self.neo4j.get_categories_from_waste(top_waste_id)
                    for category_id in category_ids:
                        all_bins.extend(self.neo4j.get_bins_for_category(category_id))
            elif search_level == "category":
                category_id = self.search_helper.get_category_from_keyword(keyword, self.index_name)
                if category_id:
                    category_ids = [category_id]
                    all_bins.extend(self.neo4j.get_bins_for_category(category_id))
            else:
                raise ValueError("Invalid search_level. Expected 'waste' or 'category'.")

            result_map[keyword] = {
                "Categories": category_ids,
                "Bins": list(set(all_bins)) if all_bins else []
            }

        return {
            "strategy": "fulltext",
            "data": result_map
        }


class VectorSearchStrategy(SearchStrategy):
    def __init__(self, neo4j_handler: Neo4jHandler, embedding_handler: VectorEmbeddingHandler,
                 index_handler: IndexHandler, search_helper: SearchHelper):
        self.neo4j = neo4j_handler
        self.embedding_handler = embedding_handler
        self.index_handler = index_handler
        self.search_helper = search_helper
        self.index_name = "waste_vector_index"
        self.label = "Waste"
        self.property = "embedding"
        self.embedding_dim = 3072
        self.similarity = "cosine"

        index_handler.ensure_vector_index(self.index_name, self.label, self.property, self.embedding_dim,
                                          self.similarity)

    def search(self, query: Any, search_level: Optional[str] = None) -> SearchResult:
        if not isinstance(query, list) or not all(isinstance(word, str) for word in query):
            raise ValueError("FulltextSearchStrategy expects a list of strings as input.")

        result_map: Dict[str, Dict[str, List[str]]] = {}
        for keyword in query:
            category_ids = []
            all_bins = []
            embedding = self.embedding_handler.get_embedding(keyword)

            results = self.search_helper.get_waste_from_keyword(keyword, self.index_name, "1", "vector", embedding)
            if not results:
                result_map[keyword] = {"Categories": [], "Bins": []}
                continue
            top_waste_id = results[0]["waste_id"]
            if top_waste_id:
                category_ids = self.neo4j.get_categories_from_waste(top_waste_id)
                for category_id in category_ids:
                    all_bins.extend(self.neo4j.get_bins_for_category(category_id))

            result_map[keyword] = {
                "Categories": category_ids,
                "Bins": list(set(all_bins)) if all_bins else []
            }

        return {
            "strategy": "vector",
            "data": result_map
        }


class SmartSearchStrategy(SearchStrategy):
    def __init__(self, neo4j: Neo4jHandler, embedding_handler: VectorEmbeddingHandler,
                 search_helper: SearchHelper, smart_ai_handler: OpenAISmartSearchHandler):
        self.neo4j = neo4j
        self.embedding_handler = embedding_handler
        self.search_helper = search_helper
        self.smart_ai = smart_ai_handler

    def search(self, query: Any, search_level: Optional[str] = None) -> SearchResult:
        if not isinstance(query, list) or not all(isinstance(word, str) for word in query):
            raise ValueError("SmartSearchStrategy expects a list of strings as input.")

        result_map: Dict[str, Dict[str, List[str]]] = {}
        for keyword in query:
            fulltext_results = self.search_helper.get_waste_from_keyword(
                keyword, index_name="fulltext_id_normalized_index", limit="5", search_type="fulltext")
            embedding = self.embedding_handler.get_embedding(keyword)
            vector_results = self.search_helper.get_waste_from_keyword(
                keyword, index_name="waste_vector_index", limit="5", search_type="vector", embedding=embedding)

            if not fulltext_results and not vector_results:
                result_map[keyword] = {"Categories": [], "Bins": []}
                continue

            fulltext_top = fulltext_results[0]["waste_id"] if fulltext_results else None
            vector_top = vector_results[0]["waste_id"] if vector_results else None

            chosen_id = None
            if fulltext_top == vector_top:
                chosen_id = fulltext_top
            elif fulltext_top and vector_top:
                fulltext_ids = [r["waste_id"] for r in fulltext_results]
                vector_ids = [r["waste_id"] for r in vector_results]
                chosen_id = self.smart_ai.ask_for_best_match(keyword, fulltext_ids, vector_ids)

            if chosen_id:
                all_bins = []
                category_ids = self.neo4j.get_categories_from_waste(chosen_id)
                for category_id in category_ids:
                    all_bins.extend(self.neo4j.get_bins_for_category(category_id))

                result_map[keyword] = {
                    "Categories": category_ids,
                    "Bins": list(set(all_bins)) if all_bins else []
                }

        return {
            "strategy": "smart",
            "data": result_map
        }


class BarcodeSearchStrategy(SearchStrategy):
    def __init__(self, fulltextStrategy: FulltextSearchStrategy):
        self.fulltext_strategy = fulltextStrategy

    def search(self, query: Any, search_level: Optional[str] = None) -> SearchResult:
        if not isinstance(query, dict) or "objects" not in query:
            raise ValueError("BarcodeSearchStrategy expects a JSON object with an 'objects' list.")

        results = []

        for obj in query["objects"]:
            material = obj.get("material")
            name = obj.get("name", "unknown")

            if not material:
                results.append({
                    "name": name,
                    "Categories": [],
                    "Bins": []
                })
                continue

            search_result = self.fulltext_strategy.search([material], "category")
            entry = search_result["data"].get(material, {})

            results.append({
                "name": name,
                "Categories": entry.get("Categories", []),
                "Bins": entry.get("Bins", [])
            })

        return {
            "strategy": "barcode",
            "data": results
        }
