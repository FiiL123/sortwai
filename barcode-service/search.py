import typing

class SearchServiceProxy:
    def search(self, context: 'BarcodeCO'):
        pass


class BarcodeCO:
    def __init__(self, name: str, manufacturer:str, material: str, parts: list[str], material_code: str, extra: str):
        self.name = name
        self.manufacturer = manufacturer
        self.material = material
        self.parts = parts
        self.material_code = material_code
        self.extra = extra
