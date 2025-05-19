from fastapi import UploadFile
from PIL import Image
from proxies import BarcodeServiceProxy, OpenAIVisionProxy, SearchServiceProxy
from pyzbar.pyzbar import Decoded, decode


class Handler:
    def __init__(self) -> None:
        self._next = None

    def handle(self, file: UploadFile, context: dict):
        raise NotImplementedError()

    def set_next(self, handler: "Handler") -> None:
        self._next = handler

    @property
    def next(self) -> "Handler":
        if not self._next:
            return NullHandler()
        return self._next


class NullHandler(Handler):
    def handle(self, file: UploadFile, context: dict):
        return None


class ImageResizeHandler(Handler):
    def handle(self, file: UploadFile, context: dict):
        im = Image.open(file.file)
        width, height = im.size
        scale_factor = 512 / min(width, height)
        im = im.resize((int(width * scale_factor), int(height * scale_factor)))
        im = im.convert("RGB")

        context["image"] = im
        return self.next.handle(file, context)


class BarcodeRecognitionHandler(Handler):
    def __init__(self) -> None:
        super().__init__()
        self.barcode_service = BarcodeServiceProxy()

    def handle(self, file: UploadFile, context: dict):
        assert "image" in context
        image: Image.Image = context["image"]
        detected_codes: list[Decoded] = decode(image)

        for code in detected_codes:
            resp = self.barcode_service.search(code.data)
            if resp is not None:
                return resp

        return self.next.handle(file, context)


class OpenAIRecognizeHandler(Handler):
    SYSTEM_PROMPT = "You are an object recognition expert. Look at the provided image and describe the object it in a few words in Slovak that can be used in waste recycling. Output just the words, nothing else."

    def __init__(self) -> None:
        super().__init__()
        self.search_service = SearchServiceProxy()
        self.openai_service = OpenAIVisionProxy(self.SYSTEM_PROMPT)

    def handle(self, file: UploadFile, context: dict):
        assert "image" in context
        image: Image.Image = context["image"]

        recognition = self.openai_service.send_image(image)
        if not recognition:
            return self.next.handle(file, context)

        response = self.search_service.search(recognition)
        return response


def get_chain() -> Handler:
    prototype = [ImageResizeHandler, BarcodeRecognitionHandler, OpenAIRecognizeHandler]
    chain = []

    for klass in prototype:
        handler = klass()
        if len(chain) != 0:
            chain[-1].set_next(handler)
        chain.append(handler)

    return chain[0]
