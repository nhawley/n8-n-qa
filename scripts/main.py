from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
from your_script import process_data

app = FastAPI(title="Python Service for n8n")

# Define your request body shape
class ProcessRequest(BaseModel):
    name: str = "World"
    numbers: list[float] = []

class ProcessResponse(BaseModel):
    message: str
    sum: float
    count: int
    average: float

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/process", response_model=ProcessResponse)
def process(request: ProcessRequest):
    try:
        result = process_data(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
