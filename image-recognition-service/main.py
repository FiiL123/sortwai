from fastapi import FastAPI, UploadFile
from handlers import get_chain

app = FastAPI()


@app.post("/recognize/")
def recognize_image(image: UploadFile):
    chain = get_chain()
    return chain.handle(image, {})
