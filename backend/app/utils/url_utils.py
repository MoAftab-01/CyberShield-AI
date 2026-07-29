from urllib.parse import urlparse
import ipaddress


SUSPICIOUS_KEYWORDS = {
    "login",
    "verify",
    "bank",
    "secure",
    "account",
    "signin",
    "update",
    "payment",
}


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)

    return bool(parsed.scheme and parsed.netloc)


def uses_https(url: str) -> bool:
    return url.lower().startswith("https://")


def extract_domain(url: str) -> str:

    parsed = urlparse(url)

    return parsed.hostname or ""


def contains_ip(url: str) -> bool:

    domain = extract_domain(url)

    try:
        ipaddress.ip_address(domain)
        return True

    except ValueError:
        return False


def url_length(url: str) -> int:
    return len(url)


def detect_keywords(url: str):

    lower = url.lower()

    detected = []

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in lower:
            detected.append(keyword)

    return detected


def count_subdomains(domain: str) -> int:

    if not domain:
        return 0

    return max(len(domain.split(".")) - 2, 0)

def calculate_url_risk(
    https: bool,
    contains_ip_address: bool,
    keywords: list[str],
    length: int,
    subdomains: int,
):

    score = 100

    recommendations = []

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

    if keywords:
        score -= 15
        recommendations.append(
            "URL contains suspicious keywords."
        )

    if length > 120:
        score -= 10
        recommendations.append(
            "Very long URLs may hide malicious intent."
        )

    if subdomains >= 3:
        score -= 15
        recommendations.append(
            "Too many subdomains detected."
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