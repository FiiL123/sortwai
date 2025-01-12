# from neo4j import GraphDatabase
from fastapi import FastAPI
import requests
from pydantic import BaseModel


app = FastAPI()

API_URL = ...
API_KEY = ...
DATABASE_URL = ...
AUTH = ... #database details ("database_name", "password")


class City(BaseModel):
    name: str

class Request(BaseModel):
    contents: str

@app.get("/hi")
def getRoot():
    return {"Hello": "There"}
@app.post("/")
def getResponse(city: City, request: Request):
    wasteTypes = getWasteTypes()
    chatHeaders = {
        "api-key": API_KEY,
        "Content-Type": "application/json",
    }

    chatData = {
        "model": "gpt-4o-mini",
        "messages":[
            {"role": "system",
             "content": """Here is a list of recyclable waste: """ + "\n".join(wasteTypes)},

            {"role": "system",
             "content": """
             ##TASK##
             """}],
        "temperature": 0.3,
        "max_tokens": 500
    }

    # response = requests.post(API_URL, headers=chatHeaders, json=chatData)
    response = requests.Response() #testing
    response.status_code = 200
    if response.status_code == 200:
        #response_content = response.json()["choices"][0]["message"]["content"]
        response_content = "JustForTesting"
        if response_content != "Not found":
            query = getCypherQuery(response_content)
            databaseResponse = queryDatabase(query)
            return databaseResponse

    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return {"Hello": "World"}


def getCypherQuery(waste: str):
    return "Hi"


def getWasteTypes():
    return ["papier", "plast", "kov"]
    with GraphDatabase.driver(DATABASE_URL, auth=AUTH) as driver:
        databaseResponse = driver.execute_query("""MATCH""")


def queryDatabase(query: str):
    return {
        "bin": "yellow",
        "extra": "Yellow snow is not for eating"
    }
    with GraphDatabase.driver(DATABASE_URL, auth=AUTH) as driver:
        databaseResponse = driver.execute_query(query)

        print(databaseResponse)