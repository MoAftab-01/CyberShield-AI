from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from fastapi.responses import FileResponse

from app.services.document_service import (
    DocumentService,
)

from app.services.document_extractor import (
    DocumentExtractor,
)
from app.services.document_index_service import (
    DocumentIndexService,
)
router = APIRouter(
    prefix="/uploads",
    tags=["Document Upload"],
)


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
):

    try:

        document = await DocumentService.save_uploaded_file(
            file
    )

        DocumentIndexService.index_document(
    file_path=document["path"],
    filename=document["original_filename"],
)

        return {
    **document,
    "message": "Upload successful and indexed.",
    }   

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/")
def list_documents():

    return DocumentService.list_files()


@router.get("/{filename}")
def download_document(
    filename: str,
):

    file = DocumentService.get_file_path(
        filename
    )

    if file is None:

        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return FileResponse(file)


@router.delete("/{filename}")
def delete_document(
    filename: str,
):

    success = DocumentService.delete_file(
        filename
    )

    if not success:

        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return {
        "message": "File deleted."
    }


# ==========================================
# Temporary Endpoint
# Test Document Extraction
# ==========================================

@router.post("/extract/{filename}")
def extract_document_text(
    filename: str,
):

    file = DocumentService.get_file_path(
        filename
    )

    if file is None:

        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    try:

        text = DocumentExtractor.extract_text(
            str(file)
        )

        return {
            "filename": filename,
            "characters": len(text),
            "preview": text[:1000],
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )