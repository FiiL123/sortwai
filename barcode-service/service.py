from .database import SortWAIBarcodeDatabase
from .search import BarcodeCO, SearchServiceProxy

class BarcodeSearchService:

    def __init__(self):
        self.db = SortWAIBarcodeDatabase()
        self.search_service = SearchServiceProxy()

    def get_products(self,barcode)-> list[BarcodeCO]:
        response = self.db.query(barcode)
        results = [BarcodeCO(*row) for row in response]
        return results

    def search(self,barcode):
        products = self.get_products(barcode)
        return self.search_service.search(products)

