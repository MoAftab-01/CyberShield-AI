from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile


class DocumentService:

    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    @staticmethod
    async def save_uploaded_file(file: UploadFile):

        extension = Path(file.filename).suffix.lower()

        if extension not in DocumentService.ALLOWED_EXTENSIONS:
            raise ValueError(
                "Only PDF, DOCX and TXT files are supported."
            )

        filename = file.filename
        destination = (
            DocumentService.UPLOAD_DIR / filename
        )

        with destination.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        return {
            "filename": filename,
            "original_filename": file.filename,
            "size": destination.stat().st_size,
            "path": str(destination),
        }

    @staticmethod
    def list_files():

        files = []

        for file in DocumentService.UPLOAD_DIR.iterdir():

            if file.is_file():

                files.append(
                    {
                        "filename": file.name,
                        "size": file.stat().st_size,
                    }
                )

        return files

    @staticmethod
    def delete_file(filename: str):

        file = (
            DocumentService.UPLOAD_DIR / filename
        )

        if not file.exists():
            return False

        file.unlink()

        return True

    @staticmethod
    def get_file_path(filename: str):

        file = (
            DocumentService.UPLOAD_DIR / filename
        )

        if not file.exists():
            return None

        return file