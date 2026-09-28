"""CISA Known Exploited Vulnerabilities (KEV) client.

The KEV feed is a single ~2MB JSON document containing every vulnerability
CISA has confirmed as exploited in the wild. Two consequences shape this
module:

* **Cache the catalog.** Fetching 2MB per lookup is wasteful, and the previous
  implementation did exactly that. A small in-process TTL cache means one
  fetch serves every request in the window - important on free-tier hosting
  with limited outbound bandwidth and slow cold starts.
* **Never present a failed lookup as a negative answer.** "Not in the KEV
  catalog" and "we could not reach CISA" are very different statements in a
  security context. The old code collapsed both into
  ``known_exploited: False``, which could tell an analyst a vulnerable system
  was fine when the check had actually failed. We keep the original keys for
  backwards compatibility and add ``lookup_status`` so callers can tell the
  difference.
"""

import threading
import time

import requests

CISA_KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)

#: How long a fetched catalog stays valid, in seconds.
CATALOG_TTL_SECONDS = 3600

NOT_FOUND_RESULT = {
    "known_exploited": False,
    "due_date": None,
    "required_action": None,
    "vendor_project": None,
    "product": None,
    "ransomware_use": None,
}


class CISAClient:

    _lock = threading.Lock()
    _catalog: dict | None = None
    _catalog_by_cve: dict[str, dict] | None = None
    _fetched_at: float = 0.0

    # -- catalog handling -------------------------------------------------

    @classmethod
    def _load_catalog(cls) -> tuple[dict[str, dict] | None, str]:
        """Return (index_by_cve_id, status).

        ``status`` is ``"ok"`` when the catalog is usable and
        ``"unavailable"`` when CISA could not be reached.
        """

        now = time.time()

        with cls._lock:
            if (
                cls._catalog_by_cve is not None
                and (now - cls._fetched_at) < CATALOG_TTL_SECONDS
            ):
                return cls._catalog_by_cve, "ok"

        try:
            response = requests.get(CISA_KEV_URL, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except Exception as error:  # network, HTTP, or malformed JSON
            print(f"CISA Client Error: {error}")
            # Serve a stale catalog if we have one rather than failing.
            with cls._lock:
                if cls._catalog_by_cve is not None:
                    return cls._catalog_by_cve, "stale"
            return None, "unavailable"

        index: dict[str, dict] = {}
        for vulnerability in payload.get("vulnerabilities", []):
            cve_id = vulnerability.get("cveID")
            if cve_id:
                index[cve_id.upper()] = vulnerability

        with cls._lock:
            cls._catalog = payload
            cls._catalog_by_cve = index
            cls._fetched_at = time.time()

        return index, "ok"

    # -- public API -------------------------------------------------------

    @staticmethod
    def get_kev(cve_id: str):
        """Look up one CVE in the KEV catalog.

        Returns the original response shape so existing callers keep working,
        plus ``lookup_status``.
        """

        index, status = CISAClient._load_catalog()

        if index is None:
            return {**NOT_FOUND_RESULT, "lookup_status": "unavailable"}

        vulnerability = index.get((cve_id or "").upper())

        if vulnerability is None:
            return {**NOT_FOUND_RESULT, "lookup_status": status}

        return {
            "known_exploited": True,
            "due_date": vulnerability.get("dueDate"),
            "required_action": vulnerability.get("requiredAction"),
            "vendor_project": vulnerability.get("vendorProject"),
            "product": vulnerability.get("product"),
            "ransomware_use": vulnerability.get("knownRansomwareCampaignUse"),
            "lookup_status": status,
        }

    @staticmethod
    def get_recent_kev(limit: int = 10) -> list[dict]:
        """Return the most recently added KEV entries, newest first.

        This is what makes "what are the latest known vulnerabilities?"
        answerable from live data instead of from a model's stale training
        cutoff.
        """

        index, status = CISAClient._load_catalog()

        if index is None:
            return []

        entries = sorted(
            index.values(),
            key=lambda item: item.get("dateAdded") or "",
            reverse=True,
        )

        return [
            {
                "cve": entry.get("cveID"),
                "vendor": entry.get("vendorProject"),
                "product": entry.get("product"),
                "vulnerability_name": entry.get("vulnerabilityName"),
                "date_added": entry.get("dateAdded"),
                "due_date": entry.get("dueDate"),
                "required_action": entry.get("requiredAction"),
                "ransomware_use": entry.get("knownRansomwareCampaignUse"),
                "short_description": entry.get("shortDescription"),
                "lookup_status": status,
            }
            for entry in entries[:limit]
        ]
