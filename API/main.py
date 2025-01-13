from neo4j import GraphDatabase
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from pydantic import BaseModel


app = FastAPI()

API_URL = ...
API_KEY = ...
DATABASE_URL = ...
AUTH = ...


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
            You are a waste classification expert specializing in recycling. Your role is to classify waste items provided by the user into one of the predefined categories listed above. Use logical deduction, common knowledge about waste materials, and the user's provided information to determine the correct category. 
            First of all, check whether the user input is not in the dedicated list. If yes, return the category name from the list only.
            ### Detailed Guidelines:
            
            1. **Analyze the Description**:
               - The waste item's description is provided in **Slovak language**. It may or may not include proper diacritics.
               - Examine the waste item's description for keywords or phrases that suggest:
                 - **Material type**: e.g., plast, papier, sklo, kov.
                 - **Condition**: čistý, kontaminovaný, mastný, použitý.
                 - **Function or usage**: e.g., obal, nádoba, kelímok.
               - Infer additional characteristics logically based on the item's described use. For example:
                 - If the user mentions "milk carton" recognize it as packaging for a liquid and infer that it might be clean or contaminated.
                 - If the user mentions "oil-stained paper" classify it as contaminated paper.
            
            2. **Determine the Most Appropriate Category**:
               - Match the waste item to the most specific and relevant category from the predefined list based on:
                 - Its primary material (e.g., plast, papier, sklo, kov).
                 - Its function or usage (e.g., obal, nádoba, položka na jedno použitie).
                 - Typical recycling practices and known properties of the material.                 
                 - Items that are **industrial, large-scale, or structural** in nature (e.g., "autovraky," "oceľový odpad," "elektroodpad") should be classified accordingly
                 - If the item could belong to multiple categories, choose the category that aligns most closely with its main material or intended use.
                 - If the predefined list contains the waste item, then return it
                 
            3. **Inference from Context**:
               - Look for contextual clues in the description that suggest additional details:
                 - If the item is described as "obal" consider what the packaging was used for (e.g., food, cosmetics, chemicals) to determine whether it might be contaminated.
                 - If the description mentions "nevratná sklenená fľaša" infer that it is recyclable glass but does not require a deposit refund.
            
            4. **Handle Composite or Mixed Materials**:
               - If the item is made from multiple materials (e.g., tetrapak, hliník s plastom), classify it based on the dominant recyclable component.
               - If no single material dominates, classify it as non-recyclable or a composite material.
            
            5. **Handle Ambiguities**:
               - If the description is too vague or lacks sufficient detail to classify confidently, respond with:
                 "Neviem presne určiť kategóriu odpadu."
               - Avoid guessing or assuming characteristics not explicitly described or logically inferred.
                 
            6. **Output Format**:
               - Return only the category name (predefined categories listed above) if a match is found.
               - For ambiguous descriptions, return:
                 "Neviem presne určiť kategóriu odpadu."
               - For non-recyclable items, return:
                 "Odpad nepatrí do recyklovateľných kategórií."

            
            ### Assumptions to Guide Your Classification:
            - Assume that common household waste items are described accurately unless explicitly stated otherwise.
            - Apply logical deduction to make reasonable assumptions about the waste based on its usage and context (e.g., "nádoba" likely held something liquid or solid).
            - Do not request additional clarification or details from the user; rely solely on the given information and recycling principles.
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
        response_content = response_content.strip().capitalize()
        print(response_content)
        #response_content = request.contents
        if response_content == "Neviem presne určiť kategóriu odpadu." or response_content == "Odpad nepatrí do recyklovateľných kategórií.":
            return JSONResponse({"bin": response_content})
        else:
            result = getBinFromQuery(response_content, city.name)
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

