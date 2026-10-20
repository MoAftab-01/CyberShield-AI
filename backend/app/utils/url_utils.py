from urllib.parse import urlparse
import ipaddress


GENERIC_SUSPICIOUS_KEYWORDS = {
    "login",
    "verify",
    "bank",
    "secure",
    "account",
    "signin",
    "update",
    "payment",
    "credential",
    "password",
    "wallet",
    "recover",
    "authenticate",
    "billing",
    "confirm",
    "support",
    "invoice",
    "crypto",
    "security",
}

BRAND_KEYWORDS = {
    "ebay",
    "paypal",
    "apple",
    "microsoft",
    "google",
    "netflix",
}

SUSPICIOUS_KEYWORDS = GENERIC_SUSPICIOUS_KEYWORDS | BRAND_KEYWORDS

ALLOWED_SCHEMES = {"http", "https"}


def is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    trimmed = url.strip()

    # Reject non-web schemes explicitly (e.g. javascript:, file:, gopher:, data:)
    if ":" in trimmed and not trimmed.lower().startswith(("http://", "https://")):
        scheme = trimmed.split(":", 1)[0].lower()
        if scheme not in ALLOWED_SCHEMES:
            return False

    candidate = trimmed
    if not (candidate.lower().startswith("http://") or candidate.lower().startswith("https://")):
        candidate = f"https://{candidate}"

    try:
        parsed = urlparse(candidate)
        return bool(parsed.scheme in ALLOWED_SCHEMES and parsed.netloc and (parsed.hostname or parsed.netloc))
    except Exception:
        return False


def uses_https(url: str) -> bool:
    return url.lower().startswith("https://")


def extract_domain(url: str) -> str:
    candidate = url.strip()
    if not (candidate.lower().startswith("http://") or candidate.lower().startswith("https://")):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    return parsed.hostname or parsed.netloc.split(":")[0] if parsed.netloc else ""


def contains_ip(url: str) -> bool:
    domain = extract_domain(url)
    try:
        ipaddress.ip_address(domain)
        return True
    except ValueError:
        return False


def is_private_or_internal_host(host_or_url: str) -> bool:
    """Detect if host points to private, loopback, link-local or cloud metadata addresses (SSRF guard)."""
    if not host_or_url:
        return False

    domain = extract_domain(host_or_url) if ("://" in host_or_url or "/" in host_or_url) else host_or_url
    domain = domain.strip().lower()

    if domain.startswith("[") and domain.endswith("]"):
        domain = domain[1:-1]
    elif ":" in domain and not ("::" in domain or domain.count(":") > 1):
        domain = domain.split(":")[0]

    if domain in {
        "localhost",
        "localhost.localdomain",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "169.254.169.254",
        "metadata.google.internal",
        "instance-data",
    }:
        return True


    if domain.endswith((".local", ".internal", ".localhost", ".lan", ".corp", ".home")):
        return True

    try:
        ip = ipaddress.ip_address(domain)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        pass

    return False


def contains_punycode(url: str) -> bool:
    domain = extract_domain(url).lower()
    return "xn--" in domain


def has_non_standard_port(url: str) -> bool:
    candidate = url.strip()
    if not (candidate.lower().startswith("http://") or candidate.lower().startswith("https://")):
        candidate = f"https://{candidate}"
    try:
        parsed = urlparse(candidate)
        return bool(parsed.port and parsed.port not in {80, 443})
    except Exception:
        return False


def url_length(url: str) -> int:
    return len(url)


def is_legitimate_brand_domain(domain: str, brand: str) -> bool:
    """Check if the domain's primary second-level domain (SLD) is the brand itself."""
    if not domain or not brand:
        return False
    clean = domain.strip().lower().split(":")[0].rstrip(".")
    parts = [p for p in clean.split(".") if p]
    if len(parts) < 2:
        return False

    two_part_tlds = {
        "co.uk", "com.au", "co.nz", "co.za", "co.in",
        "com.br", "co.jp", "gov.uk", "org.uk", "ac.uk",
    }
    joined_last_two = ".".join(parts[-2:])
    if joined_last_two in two_part_tlds and len(parts) >= 3:
        sld = parts[-3]
    else:
        sld = parts[-2]

    return sld == brand


def detect_keywords(url: str) -> list[str]:
    lower = url.lower()
    domain = extract_domain(url).lower()
    detected = []

    # Generic credential/security keywords are always flagged
    for keyword in sorted(GENERIC_SUSPICIOUS_KEYWORDS):
        if keyword in lower:
            detected.append(keyword)

    # Brand keywords are only flagged when used deceptively (subdomains, paths, or spoofed domains)
    for brand in sorted(BRAND_KEYWORDS):
        if brand in lower and not is_legitimate_brand_domain(domain, brand):
            detected.append(brand)

    return sorted(detected)


def count_subdomains(domain: str) -> int:
    if not domain:
        return 0
    # Clean port if present
    clean_domain = domain.split(":")[0]
    # For IPs, subdomain count is 0
    try:
        ipaddress.ip_address(clean_domain)
        return 0
    except ValueError:
        pass

    parts = [p for p in clean_domain.split(".") if p]
    return max(len(parts) - 2, 0)


def calculate_url_risk(
    https: bool,
    contains_ip_address: bool,
    keywords: list[str],
    length: int,
    subdomains: int,
    is_private_or_internal: bool = False,
    is_punycode: bool = False,
    has_non_standard_port: bool = False,
):
    score = 100
    recommendations = []

    if is_private_or_internal:
        score -= 40
        recommendations.append(
            "Target resolves to internal or private infrastructure (potential SSRF risk)."
        )

    if not https:
        score -= 20
        recommendations.append(
            "Use HTTPS websites whenever possible."
        )

    if contains_ip_address:
        score -= 25
        recommendations.append(
            "Avoid URLs that use raw IP addresses."
        )

    if is_punycode:
        score -= 20
        recommendations.append(
            "Punycode (xn--) detected; possible homograph or domain spoofing attack."
        )

    if has_non_standard_port:
        score -= 15
        recommendations.append(
            "URL routes through a non-standard port."
        )

    if keywords:
        score -= 15
        recommendations.append(
            "URL contains suspicious security or credential keywords."
        )

    if length > 120:
        score -= 10
        recommendations.append(
            "Very long URLs may hide malicious redirects or obfuscated payloads."
        )

    if subdomains >= 3:
        score -= 15
        recommendations.append(
            "Excessive subdomain levels detected (potential domain spoofing)."
        )

    score = max(score, 0)

    if score >= 90:
        level = "Low"
    elif score >= 70:
        level = "Medium"
    elif score >= 40:
        level = "High"
    else:
        level = "Critical"

    return score, level, recommendations