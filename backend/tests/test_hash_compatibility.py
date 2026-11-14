"""Content hashing must stay byte-identical on Python 3.10 and newer."""
import hashlib
from pathlib import Path
import pytest

pytestmark=pytest.mark.configuration_only


@pytest.mark.parametrize("content",[b"",b"\x00\xffbinary\x00",b"x"*(1024*1024+17)], ids=["empty","binary","multiple_blocks"])
def test_stamp_sha256_matches_standard_digest_without_file_digest(tmp_path,monkeypatch,content):
    monkeypatch.chdir(tmp_path)
    folder=tmp_path/"knowledge_base";folder.mkdir()
    (folder/"source.pdf").write_bytes(content)
    monkeypatch.delattr(hashlib,"file_digest",raising=False)
    from app.rag.index_meta import expected_stamp,SCHEMA_VERSION
    stamp=expected_stamp(vector_dimension=384,backend="hash",model=None)
    assert stamp["knowledge_base_sources"]==[{
        "path":"source.pdf","size":len(content),"sha256":hashlib.sha256(content).hexdigest()}]
    assert stamp["schema_version"]==SCHEMA_VERSION==4
