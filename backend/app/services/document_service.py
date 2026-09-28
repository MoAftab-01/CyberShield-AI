"""Upload storage.

Three defects were fixed here, each of which was reachable from the API:

* **Path traversal.** The destination was ``user_dir / file.filename`` with the
  client-supplied name used verbatim. A filename such as ``../../app/main.py``
  escaped the user's directory on write, and the same join was used by
  ``delete_file`` and ``get_file_path``, so an authenticated user could read
  and delete files anywhere the process could reach.
* **No size limit.** ``shutil.copyfileobj`` streamed an unbounded upload to an
  ephemeral disk. On free-tier hosting that is a denial of service against the
  whole instance, not just the uploader.
* **No name normalisation.** Two users uploading ``report.pdf`` and a single
  user uploading it twice produced silent overwrites.

The fix keeps the stream-to-disk approach - buffering a file in memory to
measure it would be worse on a 512MB instance - and enforces the limit while
copying, so an oversized upload is rejected part-way rather than after it has
already filled the disk.
"""

import os
import unicodedata
import uuid
from pathlib import Path

from fastapi import UploadFile


class DocumentService:

    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    #: 15MB. Large enough for a standards document, small enough that a handful
    #: of uploads cannot exhaust an ephemeral free-tier disk.
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 15 * 1024 * 1024))

    #: How much to read per chunk while streaming to disk.
    CHUNK_BYTES = 1024 * 1024

    @staticmethod
    def _user_directory(user_id: int) -> Path:

        directory = (
            DocumentService.UPLOAD_DIR
            / f"user_{int(user_id)}"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    # ------------------------------------------------------------------

    @staticmethod
    def safe_filename(filename: str | None, directory: Path | None = None) -> str:
        """Reduce a client-supplied name to a safe basename.

        Takes only the final path component, so no directory separator or
        ``..`` survives regardless of which convention the client used, and
        strips control characters.

        The name is preserved when it is already safe and unused, because it
        appears in citations and download links and a hashed name would be a
        visible regression. Only a collision - the same user uploading the same
        name twice - earns a short random suffix, which is what stopped the
        silent overwrite.
        """

        candidate = (filename or "").replace("\\", "/").split("/")[-1]

        candidate = unicodedata.normalize("NFKC", candidate)
        candidate = "".join(
            character
            for character in candidate
            if character.isprintable() and character not in {'"', "'", "\x00"}
        ).strip().strip(".")

        if not candidate:
            candidate = "upload"

        stem = Path(candidate).stem[:80] or "upload"
        extension = Path(candidate).suffix.lower()[:10]

        candidate = f"{stem}{extension}"

        if directory is None or not (directory / candidate).exists():
            return candidate

        return f"{stem}_{uuid.uuid4().hex[:8]}{extension}"

    @staticmethod
    def _resolve_within(directory: Path, filename: str) -> Path | None:
        """Join and confirm the result is still inside ``directory``.

        Belt-and-braces alongside :meth:`safe_filename`: if a future caller
        forgets to sanitise, the traversal still fails here.
        """

        try:
            candidate = (directory / filename).resolve()
            root = directory.resolve()
        except (OSError, ValueError):
            return None

        if candidate != root and root not in candidate.parents:
            return None

        return candidate

    # ------------------------------------------------------------------

    @staticmethod
    async def save_uploaded_file(
        file: UploadFile,
        user_id: int,
    ):

        extension = Path(file.filename or "").suffix.lower()

        if extension not in DocumentService.ALLOWED_EXTENSIONS:

            raise ValueError(
                "Only PDF, DOCX and TXT files are supported."
            )

        stored_name = DocumentService.safe_filename(
            file.filename,
            DocumentService._user_directory(user_id),
        )

        user_dir = DocumentService._user_directory(user_id)

        destination = DocumentService._resolve_within(user_dir, stored_name)

        if destination is None:
            raise ValueError("That filename is not allowed.")

        written = 0

        try:
            with destination.open("wb") as buffer:

                while True:

                    chunk = await file.read(DocumentService.CHUNK_BYTES)

                    if not chunk:
                        break

                    written += len(chunk)

                    if written > DocumentService.MAX_UPLOAD_BYTES:
                        raise ValueError(
                            "The file exceeds the "
                            f"{DocumentService.MAX_UPLOAD_BYTES // (1024 * 1024)}MB "
                            "upload limit."
                        )

                    buffer.write(chunk)

        except Exception:
            # A rejected or interrupted upload must not leave a partial file
            # behind, or the index would later be rebuilt from a truncated PDF.
            destination.unlink(missing_ok=True)
            raise

        return {
            "filename": stored_name,
            "original_filename": file.filename,
            "size": written,
            "path": str(destination),
        }

    @staticmethod
    def list_files(
        user_id: int,
    ):

        user_dir = DocumentService._user_directory(user_id)

        files = []

        for file in sorted(user_dir.iterdir()):

            if file.is_file() and not file.name.startswith("."):

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

        user_dir = DocumentService._user_directory(user_id)

        file = DocumentService._resolve_within(user_dir, filename)

        if file is None or not file.is_file():

            return False

        file.unlink()

        return True

    @staticmethod
    def get_file_path(
        user_id: int,
        filename: str,
    ):

        user_dir = DocumentService._user_directory(user_id)

        file = DocumentService._resolve_within(user_dir, filename)

        if file is None or not file.is_file():

            return None

        return file
