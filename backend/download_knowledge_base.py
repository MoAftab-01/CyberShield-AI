"""Download a small, curated set of official NIST PDFs into the local KB.

This is an explicit maintenance command, never part of application startup.
Each URL is pinned to the official NIST publication host and each response is
size-limited and checked for a PDF signature before it can replace a file.
"""

import argparse
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BACKEND_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BACKEND_DIR / "knowledge_base"
MAX_PDF_BYTES = 15 * 1024 * 1024

PUBLICATIONS = (
    (
        "Governance",
        "NIST-SP-800-63B-4.pdf",
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63b-4.pdf",
    ),
    (
        "Secure_Development",
        "NIST-SP-800-218.pdf",
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf",
    ),
    (
        "Cloud_and_Architecture",
        "NIST-SP-800-190.pdf",
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf",
    ),
    (
        "Governance",
        "NIST-SP-800-171r3.pdf",
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r3.pdf",
    ),
    (
        "Governance",
        "NIST-SP-800-161r1-upd1.pdf",
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-161r1-upd1.pdf",
    ),
)


def download_publication(folder: str, filename: str, url: str, force: bool) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "nvlpubs.nist.gov":
        raise ValueError(f"Refusing non-official NIST URL: {url}")

    destination = KNOWLEDGE_BASE_DIR / folder / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        if destination.read_bytes()[:5] != b"%PDF-":
            raise ValueError(f"Existing file is not a PDF: {destination}")
        print(f"Already present: {destination.relative_to(BACKEND_DIR)}")
        return destination

    request = Request(url, headers={"User-Agent": "CyberShieldAI-KB-maintenance/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    total = 0

    try:
        with urlopen(request, timeout=45) as response, temporary.open("wb") as output:
            if urlparse(response.geturl()).hostname != "nvlpubs.nist.gov":
                raise ValueError("NIST download redirected to an untrusted host")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_PDF_BYTES:
                raise ValueError(f"PDF exceeds {MAX_PDF_BYTES} byte limit: {filename}")

            while block := response.read(64 * 1024):
                total += len(block)
                if total > MAX_PDF_BYTES:
                    raise ValueError(f"PDF exceeds {MAX_PDF_BYTES} byte limit: {filename}")
                output.write(block)

        if total < 5 or temporary.read_bytes()[:5] != b"%PDF-":
            raise ValueError(f"Downloaded content is not a PDF: {filename}")

        temporary.replace(destination)
        print(f"Downloaded {destination.relative_to(BACKEND_DIR)} ({total:,} bytes)")
        return destination
    except (OSError, URLError, ValueError):
        temporary.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing PDFs with the current official publication files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list the pinned publications without downloading them",
    )
    args = parser.parse_args()

    for folder, filename, url in PUBLICATIONS:
        if args.dry_run:
            print(f"{folder}/{filename} <- {url}")
        else:
            download_publication(folder, filename, url, force=args.force)


if __name__ == "__main__":
    main()