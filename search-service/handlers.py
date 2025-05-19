from neo4j import GraphDatabase
from typing import List, Optional, Dict, Any, TypedDict


class Neo4jHandler:
    def __init__(self, uri: str = "bolt://127.0.0.1:7687",
                 username: str = "neo4j",
                 password: str = "bitnami1"):
        self.uri = uri
        self.username = username
        self.password = password
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

    def close(self):
        self._driver.close()
