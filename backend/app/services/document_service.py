from pathlib import Path
import shutil

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
    def _user_directory(user_id: int) -> Path:

        directory = (
            DocumentService.UPLOAD_DIR
            / f"user_{user_id}"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    @staticmethod
    async def save_uploaded_file(
        file: UploadFile,
        user_id: int,
    ):

        extension = Path(file.filename).suffix.lower()

        if extension not in DocumentService.ALLOWED_EXTENSIONS:

            raise ValueError(
                "Only PDF, DOCX and TXT files are supported."
            )

        user_dir = DocumentService._user_directory(
            user_id
        )

        destination = user_dir / file.filename

        with destination.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        return {
            "filename": file.filename,
            "original_filename": file.filename,
            "size": destination.stat().st_size,
            "path": str(destination),
        }

    @staticmethod
    def list_files(
        user_id: int,
    ):

        user_dir = DocumentService._user_directory(
            user_id
        )

        files = []

        for file in user_dir.iterdir():

            if file.is_file():

                files.append(
                    {
                        "filename": file.name,
                        "size": file.stat().st_size,
                    }
                )

        return files

    @staticmethod
    def delete_file(
        user_id: int,
        filename: str,
    ):

        file = (
            DocumentService._user_directory(
                user_id
            )
            / filename
        )

        if not file.exists():

            return False

        file.unlink()

        return True

    @staticmethod
    def get_file_path(
        user_id: int,
        filename: str,
    ):

        file = (
            DocumentService._user_directory(
                user_id
            )
            / filename
        )

        if not file.exists():

            return None

        return file