"""Fixed-origin, read-only intelligence. Live mode requires operator opt-in.

Fixture mode never silently falls back to live HTTP. No model downloads.
"""
from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from datetime import timedelta, datetime, timezone
import json
import time

import requests
from app.agents.cve_input import validate_cve
from app.knowledge.registry import SourceRegistry

MAX_BYTES = 5_000_000
# Public intelligence only; bounded process-local cache, never user documents.
_LIVE_CACHE = OrderedDict()
_NEXT_REQUEST = {}
_LIVE_LOCK = RLock()


def validate_live_payload(source, payload, cve):
    if not isinstance(payload, dict) or not isinstance(payload.get("vulnerabilities"), list):
        raise ValueError("Invalid intelligence envelope.")
    entries = payload["vulnerabilities"]
    if source == "nvd":
        if len(entries) > 1 or type(payload.get("totalResults")) is not int or payload["totalResults"] != len(entries):
            raise ValueError("Unexpected NVD result count.")
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("cve"), dict) or entry["cve"].get("id") != cve:
                raise ValueError("Mismatched NVD record.")
    else:
        if (not isinstance(payload.get("catalogVersion"), str)
                or not isinstance(payload.get("dateReleased"), str)
                or type(payload.get("count")) is not int or payload["count"] != len(entries)
                or not entries or len(entries) > 20000):
            raise ValueError("Incomplete KEV catalog.")
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("Invalid KEV entry.")
            identifier = validate_cve(entry.get("cveID"))
            if identifier in seen:
                raise ValueError("Duplicate KEV entry.")
            seen.add(identifier)
    return payload


class OfflineIntelligence:
    fixture = True

    def lookup(self, source, cve):
        validate_cve(cve)
        if cve not in {"CVE-2021-44228", "CVE-2023-44487", "CVE-2024-3094"}:
            return ({"vulnerabilities": []} if source == "nvd" else
                    {"catalogVersion": "synthetic-demo-1", "dateReleased": datetime.now(timezone.utc).date().isoformat(),
                     "vulnerabilities": []})
        if source == "nvd":
            # Explicit original synthetic fixture prose, not redistributed NVD text.
            descriptions = {
                "CVE-2021-44228": "Synthetic Log4Shell scenario: vulnerable logging components may allow remote code execution; confirm installed versions and exposure.",
                "CVE-2023-44487": "Synthetic HTTP/2 Rapid Reset scenario: affected servers may experience denial of service; confirm vendor guidance and deployed versions.",
                "CVE-2024-3094": "Synthetic XZ scenario: selected compromised releases require careful inventory and vendor review; actual asset impact is not established."}
            return {"vulnerabilities": [{"cve": {"id": cve, "published": "2024-04-01T00:00:00Z",
                "lastModified": "2024-04-02T00:00:00Z", "vulnStatus": "Analyzed",
                "descriptions": [{"lang": "en", "value": cve + ": " + descriptions[cve]}]}}]}
        if source != "cisa-kev":
            raise ValueError("Unknown source.")
        return {"catalogVersion": "synthetic-demo-1",
            "dateReleased": (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat(),
            "vulnerabilities": [] if cve == "CVE-2024-3094" else [{
                "cveID": cve,
                "shortDescription": cve + " is listed in this synthetic KEV scenario.",
                "requiredAction": "Synthetic exercise: review official vendor mitigation guidance; no automatic action is authorized."}]}


class ReadOnlyLiveIntelligence:
    fixture = False

    def __init__(self, *, approved=False):
        if approved is not True:
            raise ValueError("Live intelligence requires explicit operator approval.")
        self.retrieved_at = None

    def lookup(self, source, cve):
        validate_cve(cve)
        if source not in {"nvd", "cisa-kev"}:
            raise ValueError("Unknown source.")
        definition = SourceRegistry().get(source)
        key = (source, cve if source == "nvd" else "catalog")
        now = time.monotonic()
        with _LIVE_LOCK:
            cached = _LIVE_CACHE.get(key)
            if cached and now < cached[0]:
                _LIVE_CACHE.move_to_end(key)
                self.retrieved_at = cached[2]
                return deepcopy(cached[1])
            # NVD unauthenticated budget: at most five requests per 30 seconds
            # per process. Shared multi-worker deployments need an external gate.
            if now < _NEXT_REQUEST.get(source, 0):
                raise TimeoutError("Source rate limit; try again later.")
            _NEXT_REQUEST[source] = now + (6.1 if source == "nvd" else 1.0)
        # Fixed origins, no redirects, ambient proxy credentials or caller URLs.
        with requests.Session() as session:
            session.trust_env = False
            started = time.monotonic()
            try:
                with session.get(definition.machine_readable_url,
                    params={"cveId": cve} if source == "nvd" else None,
                    timeout=(3, 5), allow_redirects=False, stream=True,
                    headers={"Accept": "application/json", "User-Agent": "CyberShield-CVE-Investigator/1"}) as response:
                    if response.status_code == 429 or response.status_code >= 500:
                        retry = response.headers.get("Retry-After", "30")
                        delay = min(300, max(30, int(retry))) if retry.isascii() and retry.isdigit() else 30
                        with _LIVE_LOCK:
                            _NEXT_REQUEST[source] = max(_NEXT_REQUEST[source], time.monotonic() + delay)
                        raise TimeoutError("Source temporarily unavailable.")
                    if response.status_code != 200:
                        raise ValueError("Source request rejected.")
                    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                    if content_type != "application/json":
                        raise ValueError("Source did not return JSON.")
                    chunks, size = [], 0
                    limit = 1_000_000 if source == "nvd" else MAX_BYTES
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > limit or time.monotonic() - started > 10:
                            raise ValueError("Source response bound exceeded.")
                        chunks.append(chunk)
                    payload = validate_live_payload(source, json.loads(b"".join(chunks)), cve)
                    self.retrieved_at = datetime.now(timezone.utc)
                    with _LIVE_LOCK:
                        _LIVE_CACHE[key] = (time.monotonic() + (60 if source == "nvd" else 300), deepcopy(payload), self.retrieved_at)
                        _LIVE_CACHE.move_to_end(key)
                        while len(_LIVE_CACHE) > 9:
                            _LIVE_CACHE.popitem(last=False)
                    return payload
            except requests.RequestException:
                raise ConnectionError("Intelligence request unavailable.") from None
