import json
import typing

import requests


class SearchServiceProxy:
    SEARCH_API="http://search-api:8000/search"
    def search(self, context: list['BarcodeCO']):
        # request search service
        data = {
            "strategy": "barcode",
            "query": {
                "objects": [co.to_dict() for co in context]}
            ,
        }
        response = requests.post(self.SEARCH_API, data=json.dumps(data))
        data = response.json()
        return data



class BarcodeCO:
    def __init__(self, name: str, producer:str, material: str, part_name: str, material_code: str, detail: str):
        self.name = name
        self.producer = producer
        self.material = material
        self.part_name = part_name
        self.material_code = material_code
        self.detail = detail

    def to_dict(self):
        return {
            "name": self.name if self.name else "",
            "producer": self.producer if self.producer else "",
            "material": self.material if self.material else "",
            "part_name": self.part_name if self.part_name else "",
            "material_code": self.material_code if self.material_code else "",
            "detail": self.detail if self.detail else "",
        }

    def toJSON(self):
        return json.dumps(self.to_dict())