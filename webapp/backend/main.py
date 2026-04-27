"""
main.py — FastAPI application entry point.

Run with:
    cd webapp/backend
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import cases, scans, clusters, orgs

app = FastAPI(
    title="OSINT Analyser API",
    description="Backend API for the OSINT dissertation web application.",
    version="1.0.0",
)

# Allow the React dev server (and production build) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",  # fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(scans.router)
app.include_router(clusters.router)
app.include_router(orgs.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
