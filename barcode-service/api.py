from fastapi import FastAPI
from .service import BarcodeSearchService
app = FastAPI()

barcode_service = BarcodeSearchService()

@app.get("/product")
def get_product(barcode: str):
    return barcode_service.get_products(barcode)
@app.get("/search")
def search(barcode: str):
    return barcode_service.search(barcode)