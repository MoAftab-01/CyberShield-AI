from pydantic import BaseModel, Field


class URLRequest(BaseModel):
    url: str = Field(...)


class URLResponse(BaseModel):

    url: str

    is_valid_url: bool

    uses_https: bool

    contains_ip_address: bool

    domain: str

    url_length: int

    suspicious_keywords: list[str]

    subdomain_count: int

    risk_score: int

    risk_level: str

    recommendations: list[str]

    virustotal_found: bool

    virustotal_malicious: int

    virustotal_suspicious: int

    virustotal_harmless: int
    final_risk_score: int

    final_risk_level: str

    confidence: int

    analysis_summary: list[str]