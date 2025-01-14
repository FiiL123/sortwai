from neo4j import GraphDatabase
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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
             "content": """Here is a list of recyclable waste:\n            • """ + "\n            • ".join(wasteTypes) + "\n \n The waste does not have to belong to one of these categories if it is not recyclable."},

            {"role": "system",
             "content": """
             ##TASK##
            You are a recycling expert. Try to fit the user given item into one of the categories from the given list.
            You must output the exact name of the category as we use it for fulltext search. 
            Make the **first letter** after a **space** or an **_** capital. 
            
            EXAMPLES:
            Male_Kusy_Konárov -> Male_Kusy_Konárov
            Patik -> Male_Kusy_Konárov
            Čaj -> Sypané Čaje
            Podrvené Orechové Škrupinky -> Podrvené Orechové Škrupinky
             """},
            {"role": "user", "content": request.contents}
        ],
        "temperature": 0.01,
        "max_tokens": 150
    }

    response = requests.post(API_URL, headers=chatHeaders, json=chatData)
    print("got response")
    # response = requests.Response() #testing
    # response.status_code = 200 #testing
    if response.status_code == 200:
        response_content = response.json()["choices"][0]["message"]["content"]
        response_content = response_content.strip()
        print(response_content)
        #response_content = request.contents
        if response_content == "Neviem presne určiť kategóriu odpadu." or response_content == "Odpad nepatrí do recyklovateľných kategórií.":
            return JSONResponse({"bin": response_content})
        else:
            result = getBinFromQuery(response_content, city.name)
            print(result)
            if result == "Error":
                return JSONResponse({"bin": "Chýba kôš: "+response_content})
            return JSONResponse({"bin": result})

    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return {"Hello": "World"}


def getBinFromQuery(waste: str, city: str):
    print(waste)
    query = f"""MATCH (w:Waste)-[:BELONGS_IN]->(c:Category)
                WHERE w.id = "{waste}"
                WITH c
                Match (c:Category)-[:BELONGS_IN]->(b:Bin)
                WITH b
                MATCH (d:Document)-[:MENTIONS]->(w:Waste)
                WHERE d.municipality = "{city}"
                RETURN DISTINCT b"""
    with GraphDatabase.driver(DATABASE_URL, auth=AUTH) as driver:
        databaseResponse = driver.execute_query(query)
        print(databaseResponse)
        resultBin= "Error"
        for record in databaseResponse.records:
            node = record["b"]
            if node is not None:
                resultBin = node["id"]
                print(resultBin)
            else:
                resultBin = "None"
                print("Node 'b' is None.")
        print("Returning Query")
        return resultBin


def getWasteTypes():
    print("Get Waste Types")
    with GraphDatabase.driver(DATABASE_URL, auth=AUTH) as driver:
        databaseResponse = driver.execute_query("""MATCH (w:Waste)-[:BELONGS_IN]-(a)
                                                    RETURN w""")
        wasteTypes = []
        for record in databaseResponse.records:
            wasteTypes.append(record["w"]["id"])
    print("Return Waste Types")
    return wasteTypes

