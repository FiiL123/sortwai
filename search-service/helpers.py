from handlers import Neo4jHandler
from typing import List, Optional, Dict, Any, TypedDict
from collections import Counter
from unidecode import unidecode


class SuffixStemmerHelper:
    def __init__(self, neo4j: Neo4jHandler):
        self.neo4j = neo4j
        self.suffix_list: Optional[List[str]] = None

    def build_suffix_list(self, field: str = "id_normalized", label: Optional[str] = None,
                          min_word_len: int = 4, max_suffix_len: int = 6, top_n: int = 50) -> None:
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
        print(f"[SuffixStemmerHelper] Suffix list generated ({len(self.suffix_list)}):", self.suffix_list)

    def stem(self, word: str) -> str:
        if not self.suffix_list:
            raise ValueError("Suffix list not generated. Call build_suffix_list() first.")
        for suffix in sorted(self.suffix_list, key=len, reverse=True):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                return word[:-len(suffix)]
        return word


class SearchHelper:
    def __init__(self, neo4j_handler: Neo4jHandler, stemmer: SuffixStemmerHelper):
        self.neo4j = neo4j_handler
        self.stemmer = stemmer

    def get_waste_from_keyword(self, keyword: str, index_name: str, limit: str,
                               search_type: str, embedding: Optional[list[float]] = None) -> Optional[str]:
        if search_type == "fulltext":
            words = keyword.strip().lower().split()

            query_parts = []
            for word in words:
                original = word
                prefix = self.stemmer.stem(unidecode(word))
                query_parts.append(f"{original}~ {prefix}*")

            search_query = " ".join(query_parts)

            cypher = f"""
                        CALL db.index.fulltext.queryNodes($index, $query)
                        YIELD node, score
                        WHERE node:Waste
                        RETURN node.id AS waste_id
                        ORDER BY score DESC
                        LIMIT {limit}
                        """

            result = self.neo4j.query(cypher, {
                "index": index_name,
                "query": search_query
            })

            return result
        elif search_type == "vector":
            cypher = f"""
                    CALL db.index.vector.queryNodes('{index_name}', 5, $embedding)
                    YIELD node, score
                    RETURN node.id AS waste_id, score
                    ORDER BY score DESC
                    LIMIT {limit}
                    """

            results = self.neo4j.query(cypher, {
                "index_name": index_name,
                "embedding": embedding
            })

            return results

    def get_category_from_keyword(self, keyword: str, index_name: str) -> Optional[str]:
        words = keyword.strip().lower().split()
        query_parts = [f"{word}~ {self.stemmer.stem(unidecode(word))}*" for word in words]
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
            "index": index_name,
            "query": search_query
        })

        return result[0]["category_id"] if result else None
