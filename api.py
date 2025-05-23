#run with
#python -m uvicorn api:app --reload
import json
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI
from pydantic import BaseModel
from modelManager import PineconeModelManager 
from google.generativeai import configure, GenerativeModel
import model as m
from fastapi.middleware.cors import CORSMiddleware
import os

namespace = ""

##########################SETUP AREA ###############################
def load_config(file_path="config.json"):
    with open(file_path, "r") as file:
        config = json.load(file)
    return config

config = load_config()
gemini_api_key=config['gemini']
pinecone_api_key =config['pinecone']


#Parsing Text
#This can have an argument
#text_chunks=m.parseDocs()

#Setting up model
myModel=PineconeModelManager(pinecone_api_key, "us-east-1", "workshop") 

#myModel.upsert(myModel.embed_text(text_chunks),text_chunks)

# Setting up Gemini
configure(api_key=gemini_api_key)
gemini_model = GenerativeModel(model_name="gemini-2.0-flash")

#Example Query
#query = "How do I POST a request?" #user query
#response=m.query(query,myModel,gemini_model)
#print(response.text)

app = FastAPI()

origins = [
    "http://localhost:5500",  # React local dev
    "http://127.0.0.1:5500",  # Sometimes this is used instead
    # Add more origins if needed (like production domain)
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,  # ["*"] if you want to allow all origins (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
)

# Define the expected input JSON format
class InputData(BaseModel):
    query: str

# Define
@app.get("/")
async def serve_react():
    return FileResponse("index.html")

##########################SEX AREA ###############################
@app.post("/question-query/")
async def custom_json_response(data: InputData):
    # You can build any custom response based on the input
    # sourceDocs = len(data.sourceDocs)

# We return query to frontend    
    response=m.query(data.query,myModel,gemini_model)
    # print("RESPONSE",response)
    custom_response = {
        "response": response.text,

    }

    return custom_response


@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(status_code=400, content={"error": "Only PDF files are accepted."})
    
    # Ensure directory exists
    save_dir = "UploadedData"
    os.makedirs(save_dir, exist_ok = True)

    # Save the file
    file_path = os.path.join(save_dir, f"uploaded_{file.filename}")
    content = await file.read()

    # TODO: MAKE IT GO INTO THE FOLDER
    with open(file_path, "wb") as f:
        f.write(content)
    
    text_chunks=m.parseDocs(file_path)
    myModel.upsert(myModel.embed_text(text_chunks),text_chunks, file.filename)
    namespace = file.filename


    return {"filename": file.filename, "type": file.content_type}