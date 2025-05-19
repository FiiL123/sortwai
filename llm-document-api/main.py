import os
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
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
graph = Neo4jGraph(refresh_schema=False)
app = FastAPI()


@app.post("/import-document")
def add_to_graph(request: DocumentRequest):
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
