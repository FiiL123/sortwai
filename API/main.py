import os

import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase
from pydantic import BaseModel

app = FastAPI()

API_URL = os.environ.get("AZURE_OPENAI_ENDPOINT")
API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
DATABASE_URL = os.environ.get("NEO4J_URI")
AUTH = (
    os.environ.get("NEO4J_USERNAME"),
    os.environ.get("NEO4J_PASSWORD"),
)  # database details ("database_name", "password")


conversationManager = dict()

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
        "messages": [
            {
                "role": "system",
                "content": """Here is a list of recyclable waste:\n            • """
                + "\n            • ".join(wasteTypes)
                + "\n \n The waste does not have to belong to one of these categories if it is not recyclable.",
            },
            {
                "role": "system",
                "content": """
             ##TASK##
            You are a recycling expert. Try to fit the user given item into one of the categories from the given list.
            You must output the exact name of the category as we use it for fulltext search. 
            Make the **first letter** after a **space** or an **_** capital. 
            
            EXAMPLES:
            Input: Male_Kusy_Konárov 
            Output: Male_Kusy_Konárov
            
            Input:Patik 
            Output:Male_Kusy_Konárov
            
            Input:Čaj
            Output:Sypané Čaje
            
            Input:Podrvené Orechové Škrupinky
            Output:Podrvené Orechové Škrupinky
            
             """,
            },
            {"role": "user", "content": request.contents},
        ],
        "temperature": 0.01,
        "max_tokens": 150,
    }

    response = requests.post(API_URL, headers=chatHeaders, json=chatData)
    print("got response")
    # response = requests.Response() #testing
    # response.status_code = 200 #testing
    if response.status_code == 200:
        response_content = response.json()["choices"][0]["message"]["content"]
        response_content = response_content.strip()
        print(response_content)
        # response_content = request.contents
        if (
            response_content == "Neviem presne určiť kategóriu odpadu."
            or response_content == "Odpad nepatrí do recyklovateľných kategórií."
        ):
            return JSONResponse({"bin": response_content})
        else:
            result = getBinFromQuery(response_content, city.name)
            if "Error" in result.keys():
                return JSONResponse({"category": result["Error"], "bin": "Error"})

            response = {"response": []}
            for key, value in result.items():
                tips = generateTips(key, value[0])
                response["response"].append({"category": key, "bin": value[0], "id": value[1], "tips": tips})

            return JSONResponse(response)

    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return {"Oops": "Wrong site"}


@app.post("/chat/")
def chatWithLLM(id: str, request: Request):
    if id not in conversationManager.keys():
        conversationManager[id] = []

    conversationManager[id].append(("user", request.contents))

    chatHeaders = {
        "api-key": API_KEY,
        "Content-Type": "application/json",
    }

    chatData = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": f"""
"You are a friendly and knowledgeable waste management assistant. Your goal is to help users identify what type of waste they have and suggest the correct category for sorting or disposal.

When users provide a description of an item or waste, do the following:

    Ask clarifying questions to gather more details if needed (e.g., material type, size, condition, presence of hazardous elements, etc.).
    Analyze the description and categorize the waste.
    Provide a brief explanation for your categorization, mentioning key features of the waste that led to your conclusion.
Your responses should be:
    Clear and easy to understand.

Your response should be in plaintext, use only slovak language and proper grammar."""
            },
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    for (type, message) in conversationManager[id]:
        chatData["messages"].append({
            "role":type,
            "content":message
        })

    responseLLM = requests.post(API_URL, headers=chatHeaders, json=chatData)
    if responseLLM.status_code == 200:
        response_content = responseLLM.json()["choices"][0]["message"]["content"]
    conversationManager[id].append(("assistant", response_content))

    print(conversationManager)
    response = {"response": response_content}
    return JSONResponse(response)
    
    


def getBinFromQuery(waste: str, city: str):
    print(waste)
    query = f"""MATCH (w:Waste)-[:BELONGS_IN]->(c:Category)
                WHERE w.id = "{waste}"
                WITH c
                Match (c:Category)-[:BELONGS_IN]->(b:Bin)
                WITH b, c
                MATCH (d:Document)-[:MENTIONS]->(w:Waste)
                WHERE d.municipality = "{city}"
                RETURN DISTINCT b, c.id, c.frontend_id"""
    with GraphDatabase.driver(DATABASE_URL, auth=AUTH) as driver:
        databaseResponse = driver.execute_query(query)
        print(databaseResponse)
        result = {}
        for record in databaseResponse.records:
            node = record["b"]
            category = record["c.id"]
            frontendId = record["c.frontend_id"]
            if node is not None:
                result[category] = [node["id"], frontendId]
                print(result)
            else:
                result["Error"] = "No suitable trashbins found"
                print("Node 'b' is None.")
        print("Returning Query")
        return result


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

def generateTips(wasteType, bin):
    chatHeaders = {
        "api-key": API_KEY,
        "Content-Type": "application/json",
    }

    chatData = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": f"""You are an expert in waste management and recycling practices. Your task is to provide clear and helpful information about waste sorting.

Given the type of waste: {wasteType}, and the intended bin: {bin}, do the following:

    Provide 2-3 helpful tips for handling and preparing this waste type before disposal (e.g., cleaning, breaking it down, etc.).
    Also, provide useful insights and common mistakes when sorting this type of waste

Ensure your response is concise, practical, and friendly for users of all ages.
Please use only slovak in your answer and check your grammar. The response must be also formatted in html. As it will be a part of existing page, only use formatting tags as <h_>,<p>,<ul>,<li> and similar. Do not put it inside of a code block.

Be sure that you have generated the whole content"""
            },
        ],
        "temperature": 0.01,
        "max_tokens": 750,
    }

    response = requests.post(API_URL, headers=chatHeaders, json=chatData)
    if response.status_code == 200:
        response_content = response.json()["choices"][0]["message"]["content"]
    response_content = response_content.strip()
    return response_content
