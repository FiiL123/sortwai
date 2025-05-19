from typing import List, Optional, Dict, Any, TypedDict
from collections import Counter
from interfaces import SearchStrategy, SearchResult
from registry import search_service
from handlers import Neo4jHandler


class FulltextSearchStrategy(SearchStrategy):
    def __init__(self, neo4j_handler: Neo4jHandler):
        self.neo4j = neo4j_handler
        self.index_name = "fulltext_id_normalized_index"
        self.parameter = "id_normalized"
        self.__ensure_index_exists()
        self.suffix_list = None
        self.__ensure_suffix_list_exists()
        search_service.register("fulltext", self)

    def __ensure_index_exists(self):
        query = """
        SHOW INDEXES YIELD name, type
        WHERE name = $index_name AND type = 'FULLTEXT'
        RETURN count(*) AS count
        """
        result = self.neo4j.query(query, {"index_name": self.index_name})
        count = result[0]["count"]

        if count == 0:
            print(f"Index '{self.index_name}' not found. Creating...")
            create_index_query = f"""
            CREATE FULLTEXT INDEX {self.index_name}
            FOR (n:Category|Waste|Bin)
            ON EACH [n.id_normalized]
            """
            self.neo4j.run(create_index_query)
            print(f"Index '{self.index_name}' created.")

    def __ensure_suffix_list_exists(
            self,
            field: str = "id_normalized",
            label: Optional[str] = None,
            min_word_len: int = 4,
            max_suffix_len: int = 6,
            top_n: int = 50) -> None:

        suffix_counts = Counter()

        query = f"""
        MATCH (n{f':{label}' if label else ''})
        WHERE n.{field} IS NOT NULL
        RETURN n.{field} AS value
        """

        results = self.neo4j.query(query)

        for record in results:
            value = record["value"]
            for word in value.split():
                word = word.lower()
                if len(word) < min_word_len:
                    continue
                for i in range(1, min(max_suffix_len + 1, len(word))):
                    root = word[:-i]
                    if len(root) < 3:
                        continue
                    suffix = word[-i:]
                    suffix_counts[suffix] += 1

        self.suffix_list = [s for s, _ in suffix_counts.most_common(top_n)]
        print(f"Suffix list generated ({len(self.suffix_list)}):", self.suffix_list)

    def __stem(self, word: str) -> str:
        for suffix in sorted(self.suffix_list, key=len, reverse=True):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                return word[: -len(suffix)]
        return word

    def __get_waste_from_keyword(self, keyword: str) -> Optional[str]:
        words = keyword.strip().lower().split()

        query_parts = []
        for word in words:
            original = word
            prefix = self.__stem(word)
            query_parts.append(f"{original}~ {prefix}*")

        search_query = " ".join(query_parts)

        cypher = """
            CALL db.index.fulltext.queryNodes($index, $query)
            YIELD node, score
            WHERE node:Waste
            RETURN node.id AS category_id
            ORDER BY score DESC
            LIMIT 1
            """

        result = self.neo4j.query(cypher, {
            "index": self.index_name,
            "query": search_query
        })
        return result[0]["category_id"] if result else None

    def __get_category_from_keyword(self, keyword: str) -> Optional[str]:
        words = keyword.strip().lower().split()
        query_parts = [f"{word}~ {self.__stem(word)}*" for word in words]
        search_query = " ".join(query_parts)

        cypher = """
        CALL db.index.fulltext.queryNodes($index, $query)
        YIELD node, score
        WHERE node:Category
        RETURN node.id AS category_id
        ORDER BY score DESC
        LIMIT 1
        """

        result = self.neo4j.query(cypher, {
            "index": self.index_name,
            "query": search_query
        })

        return result[0]["category_id"] if result else None

    def search(self, query: Any, search_level: str = "waste") -> SearchResult:
        if not isinstance(query, list) or not all(isinstance(word, str) for word in query):
            raise ValueError("FulltextSearchStrategy expects a list of strings as input.")

        result_map: Dict[str, List[str]] = {}
        for keyword in query:
            all_bins = []

            if search_level == "waste":
                waste_id = self.__get_waste_from_keyword(keyword)
                if waste_id:
                    category_ids = self.neo4j.get_categories_from_waste(waste_id)
                    for category_id in category_ids:
                        all_bins.extend(self.neo4j.get_bins_for_category(category_id))
            elif search_level == "category":
                category_id = self.__get_category_from_keyword(keyword)
                if category_id:
                    all_bins.extend(self.neo4j.get_bins_for_category(category_id))
            else:
                raise ValueError("Invalid search_level. Expected 'waste' or 'category'.")

            result_map[keyword] = list(set(all_bins)) if all_bins else []

        return {
            "strategy": "fulltext",
            "data": result_map
        }


class VectorSearchStrategy(SearchStrategy):
    def search(self, query: Any) -> SearchResult:
        pass


class CypherQuerySearchStrategy(SearchStrategy):
    def search(self, query: Any) -> SearchResult:
        pass


class BarcodeSearchStrategy(SearchStrategy):
    def __init__(self, neo4j_handler: Neo4jHandler):
        self.fulltext_strategy = FulltextSearchStrategy(neo4j_handler)
        search_service.register("barcode", self)

    def search(self, query: Any) -> SearchResult:
        if not isinstance(query, dict) or "objects" not in query:
            raise ValueError("BarcodeSearchStrategy expects a JSON object with an 'objects' list.")

        results = []

        for obj in query["objects"]:
            material = obj.get("material")
            name = obj.get("name", "unknown")

            if not material:
                results.append({"name": name, "bins": []})
                continue

            search_result = self.fulltext_strategy.search([material])
            bins = search_result["data"].get(material, [])

            results.append({
                "name": name,
                "bins": bins
            })

        return {
            "strategy": "barcode",
            "data": results
        }
