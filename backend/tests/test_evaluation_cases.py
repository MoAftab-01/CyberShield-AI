import pytest

from evaluate_benchmarks import load_rag_cases, validate_gold_pages
from download_knowledge_base import download_publication
from app.rag.index_meta import expected_stamp


def test_expanded_cases_are_additive_and_have_unique_ids():
    cases = load_rag_cases()

    assert len(cases) == 29
    assert len({case["id"] for case in cases}) == len(cases)


def test_gold_pages_must_exist_in_index():
    cases = [
        {
            "relevant_pages": [
                {"source": "missing.pdf", "page": 3},
            ]
        }
    ]

    with pytest.raises(ValueError, match="missing.pdf p.3"):
        validate_gold_pages(cases, {("present.pdf", 1)})


def test_gold_pages_accept_real_indexed_page():
    cases = [
        {
            "relevant_pages": [
                {"source": "source.pdf", "page": 3},
            ]
        }
    ]

    validate_gold_pages(cases, {("source.pdf", 3)})


def test_downloader_rejects_non_nist_hosts():
    with pytest.raises(ValueError, match="non-official NIST URL"):
        download_publication(
            "General",
            "unsafe.pdf",
            "https://example.com/unsafe.pdf",
            force=False,
        )


def test_index_stamp_tracks_pdf_content_not_timestamp(tmp_path, monkeypatch):
    source = tmp_path / "knowledge_base" / "General" / "guide.txt"
    source.parent.mkdir(parents=True)
    source.write_text("first version", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    first = expected_stamp(vector_dimension=384, backend="hash", model=None)
    source.write_text("second version", encoding="utf-8")
    second = expected_stamp(vector_dimension=384, backend="hash", model=None)

    assert first["knowledge_base_sources"] != second["knowledge_base_sources"]