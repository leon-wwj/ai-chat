import app.logging_setup  # importing this module configures logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, models

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(models.router)
