from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, processing, schemas, jobs, providers

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)
app.include_router(jobs.router)
app.include_router(providers.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
