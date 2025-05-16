class BarcodeDatabase:
    def query(self, barcode):
        pass


class DummyBarcodeDatabase(BarcodeDatabase):
    def query(self, barcode):
        pass

class SortWAIBarcodeDatabase(BarcodeDatabase):
    def query(self, barcode):
        pass

class ExternalBarcodeDatabase(BarcodeDatabase):
    def query(self, barcode):
        pass