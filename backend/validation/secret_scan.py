"""Dependency-free tracked/untracked source scan. Outputs locations, never values.

This is a pattern scan, not a replacement for a maintained secret-scanning
service or a complete history/dependency security audit.
"""
from pathlib import Path
import json
from hashlib import sha256
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
patterns = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b"),
    "provider_key": re.compile(r"\b(?:gsk_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,}|AKIA[A-Z0-9]{16})\b"),
    "jwt_literal": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{16,}\b"),
    "credential_url": re.compile(r"(?:postgres(?:ql)?|mysql|https?)://[^\s/:]+:[^\s/@]+@"),
}
# Reviewed synthetic validation URLs and a documented example configuration.
# No operational dotenv file, provider token, or private key is exempt.
EXAMPLE_URL_HASHES = {'backend/.env.example': ['3de972c98bf6eb192f31d3cc1403df37662eb200a8a85f5d5594a1c5bf1933a6'], 'backend/tests/test_source_foundation.py': ['fbddae166ead16d1dd67736b19403ab1ac0095e344f663573848af911a7ce273'], 'frontend/tests/grounding.test.ts': ['29f49534516049399b98f5561f246104482d698941b28c099b1ccb597d571ffb']}

def main():
    with tempfile.TemporaryDirectory(prefix="cybershield-secret-scan-") as temporary:
        empty = Path(temporary) / "ignore"
        empty.write_text("")
        files = subprocess.check_output(["git", "-c", "core.excludesFile=" + str(empty),
            "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root).decode("utf-8").rstrip("\0").split("\0")
    findings = []
    for name in files:
        file = root / name
        if not file.is_file():
            continue
        if file.name.startswith(".env") and file.name not in {".env.example", ".env.sample"}:
            findings.append({"path": name, "line": 0, "kind": "operational_dotenv"})
        raw = file.read_bytes()
        if b"\x00" in raw:
            continue
        for number, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
            for kind, pattern in patterns.items():
                if pattern.search(line):
                    if kind == "credential_url" and all(sha256(m.group().encode()).hexdigest()
                        in EXAMPLE_URL_HASHES.get(name, ()) for m in pattern.finditer(line)):
                        continue
                    findings.append({"path": name, "line": number, "kind": kind})
    print(json.dumps({"source_files": len(files), "findings": findings,
        "scope": "tracked and non-ignored untracked source; values suppressed"}))
    return int(bool(findings))

if __name__ == "__main__":
    raise SystemExit(main())
