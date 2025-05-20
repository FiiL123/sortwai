import base64
from io import BytesIO

import requests
from openai import AzureOpenAI
from PIL.Image import Image

SEARCH_URL = "http://search-api:8000/search"
BARCODE_URL = "http://barcode:8000/search"


class BarcodeServiceProxy:
    def search(self, barcode: str) -> dict | None:
        resp = requests.get(BARCODE_URL, params={"barcode": barcode})
        resp.raise_for_status()
        return resp.json()


class SearchServiceProxy:
    def search(self, query: str) -> dict | None:
        resp = requests.post(SEARCH_URL, json={"strategy": "smart", "query": [query]})
        resp.raise_for_status()
        return resp.json()


class OpenAIVisionProxy:
    def __init__(self, system_prompt: str) -> None:
        self.client = AzureOpenAI()
        self.system_prompt = system_prompt

    def send_image(self, image: Image) -> str | None:
        data = BytesIO()
        image.save(data, "jpeg")
        data.seek(0)
        b64 = base64.b64encode(data.read()).decode()

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "content": self.system_prompt,
                    "role": "system",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        }
                    ],
                },
            ],
        )

        if len(response.choices) < 1:
            return None

        return response.choices[0].message.content
