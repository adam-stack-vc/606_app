from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.query import run_query_from_nl
import os

app = FastAPI()

# Define expected input
class QuestionInput(BaseModel):
    question: str

# Tell FastAPI to expect this in the request body
@app.post("/ask")
async def ask_question(body: QuestionInput):
    if not body.question:
        raise HTTPException(status_code=400, detail="Missing question")
    return run_query_from_nl(body.question)
