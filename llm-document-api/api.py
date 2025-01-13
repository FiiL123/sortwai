import os

from fastapi import FastAPI
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel


class DocumentRequest(BaseModel):
    document: str


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


@app.post("/llm-document")
def add_to_graph(request: DocumentRequest):
    chunks = [Document(chunk.strip()) for chunk in request.document.split("---")]
    graph_documents = llm_transformer.convert_to_graph_documents(chunks)
    graph.add_graph_documents(graph_documents, include_source=True)
    return {"graph_documents": graph_documents}
