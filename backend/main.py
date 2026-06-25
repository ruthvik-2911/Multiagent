from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes import chat, upload, documents

# ----------------------------------
# FASTAPI APP
# ----------------------------------

app = FastAPI(
    title="Enterprise Knowledge Assistant"
)

# ----------------------------------
# HEALTH CHECK
# ----------------------------------

@app.get("/health")
def health():
    return {
        "status": "running"
    }

# ----------------------------------
# ROUTERS
# ----------------------------------

app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(documents.router)

# Mount frontend directory
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
