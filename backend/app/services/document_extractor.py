from pathlib import Path

import fitz
from docx import Document


class DocumentExtractor:

    @staticmethod
    def extract_text(file_path: str):

        extension = (
            Path(file_path)
            .suffix
            .lower()
        )

        if extension == ".pdf":
            return DocumentExtractor.extract_pdf(
                file_path
            )

        if extension == ".docx":
            return DocumentExtractor.extract_docx(
                file_path
            )

        if extension == ".txt":
            return DocumentExtractor.extract_txt(
                file_path
            )

        raise ValueError(
            "Unsupported document type."
        )

    @staticmethod
    def extract_pdf(file_path: str):

        document = fitz.open(file_path)

        text = ""

        for page in document:

            text += page.get_text()

        document.close()

        return text

    @staticmethod
    def extract_docx(file_path: str):

        document = Document(file_path)

        return "\n".join(

            paragraph.text

            for paragraph in document.paragraphs

        )

    @staticmethod
    def extract_txt(file_path: str):

        with open(

            file_path,

            "r",

            encoding="utf-8",

            errors="ignore",

        ) as file:

            return file.read()