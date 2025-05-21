import os
from abc import ABC, abstractmethod
from typing import Protocol

from fastapi import FastAPI, Depends
from pydantic import BaseModel

from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_neo4j import (
    Neo4jGraph,
    Neo4jVector,
    GraphCypherQAChain,
)

cypher_prompt = PromptTemplate.from_template(
    """
You are an expert in waste management.

Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Always use "id" when trying to search something.
Always translate words in english to search something.
Use only the following id in your search query:
{id}

The graph contains nodes: Material, Bin, Instruction, Exception.
Relationships: GOES_TO, PROHIBITED_IN, HAS_INSTRUCTION, SIMILAR_TO

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}
"""
)

qa_prompt = PromptTemplate.from_template(
    """
You are a helpful assistant for waste sorting and environmental awareness.

You are connected to a Neo4j knowledge graph containing information about how to properly sort different types of waste.

The graph contains the following node types:
- Material (e.g., Paper, Plastic, Glass, Metal, Bio-waste, Textiles)
- Bin (e.g., Yellow Bin, Blue Bin, Brown Bin, Green Bin, Black Bin)
- Exception (items that must NOT be sorted into a specific bin)
- Instruction (helpful rules and recommendations)

It also contains the following relationships:
- GOES_TO: Material should be placed in a specific Bin.
- MUST_NOT_GO_TO: Material or Exception must NOT be placed in a specific Bin.
- HAS_INSTRUCTION: A Material or Bin may have related tips or rules.
- SIMILAR_TO: Materials that are closely related.

---

The user asked a question: "{question}"

You were given the following structured information retrieved from the graph:

{context}

Your task:

1. Analyze the context and identify what bins are recommended (`GOES_TO`) for the material.
2. If there are bins that are explicitly forbidden (`MUST_NOT_GO_TO`), mention them clearly.
3. If there are any instructions (`HAS_INSTRUCTION`), summarize them.
4. If no information is available about the material, politely explain that it's not recognized in the system.

---

Write a clear, friendly, and helpful answer to the user, based ONLY on the provided context.
- Do not hallucinate or assume anything outside the data.
- Be concise, direct, and easy to understand.
- If multiple options exist, list them clearly.

Format the response as a single paragraph in natural slovak language.
"""
)


class UserQuery(BaseModel):
    query: str


class EmbeddingService(Protocol):
    @property
    @abstractmethod
    def model(self):
        raise NotImplementedError


class VectorSearchService(Protocol):
    def get_closest_node_id(self, question: str, k: int = 1) -> str:
        """Return the `id` property of the closest KG node."""


class QAService(Protocol):
    def answer(self, question: str, node_id: str):
        """Return the assistant's answer."""


class OpenAIEmbeddingService:
    def __init__(self) -> None:
        self._model = AzureOpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
            azure_endpoint=os.getenv("OPENAI_EMBEDDING_ENDPOINT"),
            api_key=os.getenv("OPENAI_EMBEDDING_API_KEY"),
            openai_api_version=os.getenv("OPENAI_EMBEDDING_API_VERSION"),
        )

    @property
    def model(self):
        return self._model


class Neo4jVectorSearchService:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._vector = Neo4jVector.from_existing_graph(
            url=os.environ["NEO4J_URI"],
            embedding=embedding_service.model,
            node_label="Material",
            embedding_node_property="embedding",
            text_node_properties=["id"],
        )

    def get_closest_node_id(self, question: str, k: int = 1) -> str:
        result = self._vector.similarity_search(question, k=k)
        return result[0].page_content


class GraphQAService:
    def __init__(self, llm, graph):
        self._qa_chain = GraphCypherQAChain.from_llm(
            llm,
            graph=graph,
            verbose=True,
            allow_dangerous_requests=True,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt,
        )

    def answer(self, question: str, node_id: str):
        return self._qa_chain.invoke({"query": question, "id": node_id})


class QueryMediator:
    def __init__(
        self,
        vector_service: VectorSearchService,
        qa_service: QAService,
    ) -> None:
        self._vector_service = vector_service
        self._qa_service = qa_service

    def handle(self, query: str):
        node_id = self._vector_service.get_closest_node_id(query)
        return self._qa_service.answer(query, node_id)


_llm = AzureChatOpenAI(
    deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    temperature=0,
)
_graph = Neo4jGraph(refresh_schema=False, url=os.getenv("NEO4J_URI"))

_embedding_service = OpenAIEmbeddingService()
_vector_service = Neo4jVectorSearchService(_embedding_service)
_qa_service = GraphQAService(_llm, _graph)
_mediator = QueryMediator(_vector_service, _qa_service)

app = FastAPI()


def get_mediator() -> QueryMediator:
    return _mediator


@app.post("/query")
async def query(user_query: UserQuery, mediator: QueryMediator = Depends(get_mediator)):
    return mediator.handle(user_query.query)
