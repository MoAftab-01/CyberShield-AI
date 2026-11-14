"""Verify literal approved fixture bytes on disk or in Git's staged index."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "backend/evaluation"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", action="store_true")
    options = parser.parse_args()
    checks = []
    def raw(path):
        resolved = path.resolve()
        if not resolved.is_relative_to(BASE):
            raise ValueError("Fixture path escapes evaluation directory.")
        if options.index:
            return subprocess.check_output(["git", "show", ":" + resolved.relative_to(ROOT).as_posix()], cwd=ROOT)
        return resolved.read_bytes()
    def pinned(path, expected):
        if sha256(raw(path)).hexdigest() != expected:
            raise ValueError("Pinned fixture mismatch: " + path.relative_to(ROOT).as_posix())
        checks.append(path.relative_to(ROOT).as_posix())
    quality = BASE / "retrieval_quality"
    for folder in [BASE / "source_foundation", quality]:
        manifest = json.loads(raw(folder / "manifest.json"))
        for artifact in manifest["artifacts"]:
            pinned(folder / artifact["filename"], artifact["sha256"])
        if folder == quality:
            for name in ["queries.json", "qrels.json"]:
                pinned(folder / name, manifest[name])
    grounded = BASE / "grounded_answers"
    manifest = json.loads(raw(grounded / "manifest.json"))
    for name in ["review.json", "claim_cases.json"]:
        pinned(grounded / name, manifest[name])
    pinned(quality / "manifest.json", manifest["base_manifest_sha256"])
    review = json.loads(raw(grounded / "review.json"))
    pinned(quality / "queries.json", review["base_queries_sha256"])
    pinned(quality / "qrels.json", review["base_qrels_sha256"])
    print(json.dumps({"pinned_hash_checks": len(checks), "result": "pass",
                      "source": "Git index" if options.index else "working checkout"}))

if __name__ == "__main__":
    main()
