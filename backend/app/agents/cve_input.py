"""Canonical CVE input boundary; no database, graph or provider imports."""
import re

CVE_PATTERN = re.compile(r"CVE-[0-9]{4}-[0-9]{4,19}", re.ASCII)

def validate_cve(value):
    if not isinstance(value, str) or not CVE_PATTERN.fullmatch(value):
        raise ValueError("Use a canonical CVE identifier, for example CVE-2021-44228.")
    return value
