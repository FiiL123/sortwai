import psycopg

class BarcodeDatabase:
    def query(self, barcode):
        pass


class DummyBarcodeDatabase(BarcodeDatabase):
    def query(self, barcode):
        pass

class SortWAIBarcodeDatabase(BarcodeDatabase):
    def __init__(self):
        self.conn = psycopg.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="db",
            port="5432",
        )
        self.cursor = self.conn.cursor()

    def query(self, barcode):
        try:
            self.cursor.execute(
                "SELECT name, producer, material, part_name, material_code, detail FROM barcode.products WHERE barcode = %s;",
                (barcode,)
            )
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(f"Database query failed: {e}")
            return []

    def __del__(self):
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()

class ExternalBarcodeDatabase(BarcodeDatabase):
    def query(self, barcode):
        pass