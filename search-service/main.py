import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any, Union
from registry import search_service

app = FastAPI()


class FulltextSearchRequest(BaseModel):
    strategy: Literal["fulltext"]
    query: List[str]
    search_level: Optional[Literal["waste", "category"]] = "waste"


class BarcodeSearchRequest(BaseModel):
    strategy: Literal["barcode"]
    query: Dict[str, Any]


class VectorSearchRequest(BaseModel):
    strategy: Literal["vector"]
    query: List[str]


class SmartSearchRequest(BaseModel):
    strategy: Literal["smart"]
    query: List[str]


SearchRequest = Union[
    FulltextSearchRequest,
    BarcodeSearchRequest,
    VectorSearchRequest,
    SmartSearchRequest
]


@app.post("/search")
def search_route(request: SearchRequest):
    print(f"Search was called with request: {request}")
    try:
        if request.strategy == "fulltext":
            return search_service.search(request.strategy, request.query, search_level=request.search_level)

        return search_service.search(request.strategy, request.query)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
