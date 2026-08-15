from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from datasheet_summary import router as summary_router
from nexar_proxy import router as nexar_router   # includes /nexar/search AND /datasheet/serper

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summary_router)
app.include_router(nexar_router)