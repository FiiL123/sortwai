from docling.document_converter import DocumentConverter
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_openai import AzureChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph

import os

source = "https://www.naturpack.sk/content/16/np-alchymia-odpadu-v6-typa.pdf"  # document per local path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())

markdown = result.document.export_to_markdown()

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
        ("#", "Header1"),
        ("##", "Header2"),
        ("###", "Header3")
    ])
splitted_chunks = splitter.split_text(markdown)

filtered_chunks = [chunk for chunk in splitted_chunks if len(chunk.page_content.strip()) > 30]

llm = AzureChatOpenAI(
    deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    temperature=0,
)

llm_transformer = LLMGraphTransformer(
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

def split_into_batches(items, batch_size):
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]

all_documents = []

for batch in split_into_batches(filtered_chunks, batch_size=5):
    graph_documents = llm_transformer.convert_to_graph_documents(batch)
    all_documents.extend(graph_documents)

graph = Neo4jGraph(refresh_schema=False, url="bolt://0.0.0.0:8687")

graph.add_graph_documents(all_documents, include_source=True)
