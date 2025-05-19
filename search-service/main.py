from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from registry import search_service

app = FastAPI()


class FulltextSearchRequest(BaseModel):
    strategy: Literal["fulltext"]
    query: List[str]
    search_level: Optional[Literal["waste", "category"]] = "waste"


class BarcodeSearchRequest(BaseModel):
    strategy: Literal["barcode"]
    query: Dict[str, Any]


SearchRequest = FulltextSearchRequest | BarcodeSearchRequest


@app.post("/search")
def search_route(request: SearchRequest):
    try:
        result = search_service.search(
            request.strategy,
            request.query
        )
        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
