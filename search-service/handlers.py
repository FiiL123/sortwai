from neo4j import GraphDatabase
from typing import List, Optional, Dict, Any, TypedDict
from openai import AzureOpenAI

import os


class Neo4jHandler:
    def __init__(self, uri: str = "bolt://127.0.0.1:7687",
                 username: str = "USERNAME",
                 password: str = "PASSWORD"):
        self.uri = os.environ.get("NEO4J_URI", uri)
        self.username = os.environ.get("NEO4J_USERNAME", username)
        self.password = os.environ.get("NEO4J_PASSWORD", password)
        self._driver = None

        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

                with self._driver.session() as session:
                    session.run("RETURN 1")
                print("Successfully connected to Neo4j database")
            except Exception as e:
                print(f"Failed to connect to Neo4j: {str(e)}")
                raise ConnectionError(f"Could not connect to Neo4j database: {str(e)}")

    def query(self, cypher: str, params: Optional[Dict] = None) -> List[Dict]:
        with self._driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def run(self, cypher: str, params: Optional[Dict] = None) -> None:
        with self._driver.session() as session:
            session.run(cypher, params or {})

    def get_categories_from_waste(self, waste_id: str) -> List[str]:
        cypher = """
        MATCH (w:Waste {id: $waste_id})-[:BELONGS_IN]->(c:Category)
        RETURN c.id AS category_id
        """
        results = self.query(cypher, {"waste_id": waste_id})
        return [record["category_id"] for record in results]

    def get_bins_for_category(self, category_id: str) -> List[str]:
        cypher = """
        MATCH (c:Category {id: $category_id})-[:BELONGS_IN]->(b:Bin)
        RETURN b.id AS bin_id
        """
        results = self.query(cypher, {"category_id": category_id})
        return [record["bin_id"] for record in results]

    def query_vector(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        cypher = """
        CALL db.index.vector.queryNodes('waste_vector_index', $top_k, $embedding)
        YIELD node, score
        RETURN node.id AS waste_id, score
        """
        return self.query(cypher, {"embedding": embedding, "top_k": top_k})

    def close(self):
        self._driver.close()


class VectorEmbeddingHandler:
    def __init__(self, neo4j_handler: Neo4jHandler):
        self.neo4j = neo4j_handler

        self.client = AzureOpenAI(
            api_key=os.environ.get("OPENAI_EMBEDDING_API_KEY"),
            api_version=os.environ.get("OPENAI_EMBEDDING_API_VERSION"),
            azure_endpoint=os.environ.get("OPENAI_EMBEDDING_ENDPOINT")
        )
        self.deployment_name = "ace-text-embedding-3-large"

    def get_embedding(self, text: str) -> list[float]:
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.deployment_name
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to get embedding for '{text}': {e}")

    def embed_missing_nodes(self, label: str = "Waste", text_field: str = "id_normalized"):
        print(f"[VectorEmbeddingHandler] Checking for unembedded nodes with label '{label}'...")
        cypher = f"""
        MATCH (n:{label})
        WHERE n.embedding IS NULL AND n.id_normalized IS NOT NULL
        RETURN n.id AS id, n.{text_field} AS text
        """

        records = self.neo4j.query(cypher)
        print(f"[VectorEmbeddingHandler] Found {len(records)} nodes without embeddings.")

        for record in records:
            try:
                embedding = self.get_embedding(record["text"])
                update_query = f"""
                        MATCH (n:{label} {{id: $id}})
                        SET n.embedding = $embedding
                        """
                self.neo4j.run(update_query, {"id": record["id"], "embedding": embedding})
                print(f"[VectorEmbeddingHandler] Embedded node {record['id']}")
            except Exception as e:
                print(f"[VectorEmbeddingHandler] Failed to embed node {record['id']}: {e}")


class IndexHandler:
    def __init__(self, neo4j_handler: Neo4jHandler):
        self.neo4j = neo4j_handler

    def ensure_fulltext_index(self, index_name: str, labels: List[str], field: str):
        labels_str = "|".join(labels)
        query = """
        SHOW INDEXES YIELD name, type
        WHERE name = $index_name AND type = 'FULLTEXT'
        RETURN count(*) AS count
        """
        result = self.neo4j.query(query, {"index_name": index_name})
        if result[0]["count"] == 0:
            print(f"[IndexHandler] Creating fulltext index: {index_name}")
            create_query = f"""
            CREATE FULLTEXT INDEX {index_name}
            FOR (n:{labels_str})
            ON EACH [n.{field}]
            """
            self.neo4j.run(create_query)
            print(f"[IndexHandler] Fulltext index '{index_name}' created.")
        else:
            print(f"[IndexHandler] Fulltext index '{index_name}' already exists.")

    def ensure_vector_index(self, index_name: str, label: str, property: str, dimensions: int, similarity: str = "cosine"):
        query = """
        SHOW INDEXES YIELD name, type
        WHERE name = $index_name AND type = 'VECTOR'
        RETURN count(*) AS count
        """
        result = self.neo4j.query(query, {"index_name": index_name})
        if result[0]["count"] == 0:
            print(f"[IndexHandler] Creating vector index: {index_name}")
            create_query = f"""
            CREATE VECTOR INDEX {index_name}
            FOR (n:{label})
            ON (n.{property})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimensions},
                    `vector.similarity_function`: '{similarity}'
                }}
            }}
            """
            self.neo4j.run(create_query)
            print(f"[IndexHandler] Vector index '{index_name}' created.")
        else:
            print(f"[IndexHandler] Vector index '{index_name}' already exists.")

class OpenAISmartSearchHandler:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key="AZURE_OPENAI_API_KEY",
            api_version="OPENAI_API_VERSION",
            azure_endpoint="AZURE_OPENAI_ENDPOINT"
        )
        self.deployment_name = "ace-gpt-4o-mini"

    def ask_for_best_match(self, keyword: str, fulltext_ids: list[str], vector_ids: list[str]) -> str:
        prompt = f"""
The user searched for: '{keyword}'.

Fulltext search results:
{fulltext_ids}

Vector search results:
{vector_ids}

Which of these waste IDs best matches the user's intent? Respond with only the best Waste ID.
""".strip()

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are a waste sorting assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()
