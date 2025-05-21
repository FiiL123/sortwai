import os
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel
from unidecode import unidecode


class DocumentModel(BaseModel):
    name: str
    municipality: str
    content: str


class DocumentRequest(BaseModel):
    document: DocumentModel
    split_into_chunks: bool = True


class Category(BaseModel):
    id: str
    frontend_id: str | None = None
    municipalities: list[str] = []


class CategoryWithWaste(Category):
    waste_ok: list[str]
    waste_not: list[str]
    bins: list[str]


llm = AzureChatOpenAI(
    deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    temperature=0,
)
llm_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=["Waste", "Category", "Bin"],
    allowed_relationships=["BELONGS_IN", "PROHIBITED_IN"],
    additional_instructions="""You are building a graph for waste management and recycling.

    The document describes multiple waste categories and what bin they should be put in.
    For each category, the document can provide examples of waste items that belong to that category
    and items that do not.

    For every waste category mentioned, create a `Category` node.
    For each waste item mentioned in the document, create a `Waste` node.
    Every waste item has to be put in some bin as described by the document.
    Create a relation BELONGS_IN between each waste item and waste category it belongs to.
    Create a relation BELONGS_IN between each waste category and a node with a `Bin` label that the waste category should be recycled in.
    For every waste item that does not belongs to a particular category, create a PROHIBITED_IN relation.
    Do not create cyclic relations.
    Adhere to the previous instructions and I will give you a raise. Or else…
    """,
)

llm_transformer_for_chat = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=["Material", "Bin", "Exception", "Instruction"],
    allowed_relationships=["GOES_TO", "PROHIBITED_IN", "HAS_INSTRUCTION", "SIMILAR_TO"],
    additional_instructions="""
        You are an expert in analyzing technical environmental documentation to build a knowledge graph for waste sorting instructions.

        Your task is to read the input text and extract:

        1. Entities:
           - Material (e.g., Paper, Plastic, Glass, Bio-waste, Metal, Textiles)
           - Bin (e.g., Yellow Bin, Blue Bin, Brown Bin, Green Bin, Black Bin)
           - Exception (items that should NOT be sorted into a specific bin)
           - Instruction (actions, tips, rules for sorting)

        2. Relationships:
           - GOES_TO: Material is supposed to be placed into a specific Bin.
           - PROHIBITED_IN: Material or Exception must NOT be placed into a specific Bin.
           - HAS_INSTRUCTION: Material or Bin has an associated Instruction.
           - SIMILAR_TO: Material is similar to another material.

        Rules:
        - Generate short, factual, and precise property values.
        - If some information (examples, tips) is missing, omit the property.
        - Use unique IDs like m1, b1, e1, i1 within the same extraction.
        - Do not hallucinate information that is not explicitly stated.
        - If multiple bins are possible for the same material, create multiple GOES_TO relationships.
        - For forbidden materials (e.g., "dirty paper should not be sorted"), use the PROHIBITED_IN relationship.
    """,
)

graph = Neo4jGraph(refresh_schema=False)
graph_for_chat = Neo4jGraph(url=os.environ["NEO4J_CHAT_URI"], refresh_schema=False)
app = FastAPI()

import logging

logging.basicConfig(level=logging.INFO)


@app.post("/import-document")
def add_to_graph(request: DocumentRequest):
    def create_chat_graph(document):
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header1"),
                ("##", "Header2"),
                ("###", "Header3"),
            ]
        )
        splitted_chunks = splitter.split_text(document)

        filtered_chunks = [
            chunk for chunk in splitted_chunks if len(chunk.page_content.strip()) > 30
        ]

        def split_into_batches(items, batch_size):
            for i in range(0, len(items), batch_size):
                yield items[i : i + batch_size]

        all_documents = []

        for batch in split_into_batches(filtered_chunks, batch_size=5):
            graph_documents = llm_transformer_for_chat.convert_to_graph_documents(batch)
            all_documents.extend(graph_documents)

        graph_for_chat.add_graph_documents(all_documents, include_source=True)

        return all_documents

    document = request.document
    if request.split_into_chunks:
        chunks = [
            Document(
                chunk.strip(),
                metadata={
                    "name": document.name,
                    "municipality": document.municipality,
                    "chunk_number": n,
                },
            )
            for n, chunk in enumerate(document.content.split("---"))
        ]
    else:
        chunks = [
            Document(
                document.content.strip(),
                metadata={"name": document.name, "municipality": document.municipality},
            )
        ]
    md = open("text.md", "r").read()
    docs = create_chat_graph(md)
    print(docs)

    graph_documents = llm_transformer.convert_to_graph_documents(chunks)

    for doc in graph_documents:
        for node in doc.nodes:
            if node.id:
                normalized = unidecode(node.id.replace("_", " "))
                node.properties["id_normalized"] = normalized

    graph.add_graph_documents(graph_documents, include_source=True)

    return {"graph_documents": graph_documents}


@app.get("/categories")
def list_categories(
    municipality: str | None = None, document: str | None = None
) -> list[Category]:
    filter = ""
    params = {}
    if municipality and document:
        raise HTTPException(
            status_code=422,
            detail="Filtering by municipality and document at the same time is not supported.",
        )
    if municipality:
        filter = "{municipality: $municipality}"
        params["municipality"] = municipality
    if document:
        filter = "{name: $document}"
        params["document"] = document

    documents = graph.query(
        f"MATCH (c:Category)<-[:MENTIONS]-(d:Document {filter}) RETURN c,d.municipality as m",
        params,
    )

    categories = {}
    for doc in documents:
        id_ = doc["c"]["id"]
        if id_ not in categories:
            categories[id_] = doc["c"]

        if "municipalities" in categories[id_]:
            categories[id_]["municipalities"].add(doc["m"])
        else:
            categories[id_]["municipalities"] = {doc["m"]}

    return list(categories.values())


@app.get("/categories/{category_id}")
def category_detail(category_id: str) -> CategoryWithWaste:
    document = graph.query("MATCH (c:Category {id: $id}) RETURN c", {"id": category_id})
    if not document:
        raise HTTPException(status_code=404, detail="Category not found.")

    category = document[0]["c"]

    municipalities = graph.query(
        "MATCH (:Category {id: $id})<-[:MENTIONS]-(d:Document) RETURN d.municipality as m",
        {"id": category_id},
    )
    category["municipalities"] = [m["m"] for m in municipalities]

    wastes = graph.query(
        "MATCH (:Category {id: $id})<-[:BELONGS_IN]-(w:Waste) RETURN w",
        {"id": category_id},
    )
    category["waste_ok"] = [w["w"]["id"] for w in wastes]

    wastes_not = graph.query(
        "MATCH (:Category {id: $id})<-[:PROHIBITED_IN]-(w:Waste) RETURN w",
        {"id": category_id},
    )
    category["waste_not"] = [w["w"]["id"] for w in wastes_not]

    bins = graph.query(
        "MATCH (:Category {id: $id})-[:BELONGS_IN]->(b:Bin) RETURN b",
        {"id": category_id},
    )
    category["bins"] = [b["b"]["id"] for b in bins]

    return category


@app.post("/categories/{category_id}/frontend_id")
def set_frontend_id(category_id: str, frontend_id: Annotated[str, Body(embed=True)]):
    category = graph.query(
        "MATCH (c:Category {id: $id}) SET c.frontend_id = $feid RETURN c",
        {"id": category_id, "feid": frontend_id},
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    return "ok"
