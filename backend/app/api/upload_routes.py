from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.dependencies.auth import get_current_user

from app.services.document_service import DocumentService
from app.services.document_extractor import DocumentExtractor
from app.services.document_index_service import DocumentIndexService

router = APIRouter(
    prefix="/uploads",
    tags=["Document Upload"],
)


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):

    try:

        document = await DocumentService.save_uploaded_file(
            file=file,
            user_id=current_user.id,
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
def list_documents(
    current_user: User = Depends(get_current_user),
):

    return DocumentService.list_files(
        current_user.id
    )


@router.get("/{filename}")
def download_document(
    filename: str,
    current_user: User = Depends(get_current_user),
):

    file = DocumentService.get_file_path(
        current_user.id,
        filename,
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
    current_user: User = Depends(get_current_user),
):

    success = DocumentService.delete_file(
        current_user.id,
        filename,
    )

    if not success:

        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return {
        "message": "File deleted."
    }


@router.post("/extract/{filename}")
def extract_document_text(
    filename: str,
    current_user: User = Depends(get_current_user),
):

    file = DocumentService.get_file_path(
        current_user.id,
        filename,
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