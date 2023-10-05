from typing import Annotated 
from fastapi import FastAPI, APIRouter, Header, Body, HTTPException

app = FastAPI()

@app.get("/utils/echo")
def check(user_watches_xxx: bool = False) -> str:
    if user_watches_xxx:
        raise HTTPException(status_code=404, detail="Father not found")
    return "+1 Gigachad award"