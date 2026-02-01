from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

@app.get("/lobby")
async def root():
    return {"message": "Hello world! From FastAPI behind Apache proxy"}

@app.get("/lobby/state")
def lobby_state():
    return {"players": ["Get", "out"]}
