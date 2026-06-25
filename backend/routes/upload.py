from fastapi import APIRouter, UploadFile, File
import os
import shutil
from backend.services.indexer import index_file

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    save_path = os.path.join(
        "data",
        "Policies",
        file.filename
    )

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Immediately index the file
    index_file(save_path)

    return {
        "message": "File uploaded and indexed successfully",
        "file": file.filename
    }
