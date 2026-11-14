"""Immutable provenance and evidence contracts; no runtime service dependencies."""
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class Section(Contract):
    heading: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=100000)


class SourceDefinition(Contract):
    source_id: str
    organization: str
    canonical_url: str
    machine_readable_url: str | None = None
    licensing_url: str
    licensing_notes: str
    trust_classification: Literal["authoritative_organization", "synthetic_fixture"]

    @field_validator("canonical_url", "machine_readable_url", "licensing_url")
    @classmethod
    def safe_url(cls, value):
        if value is None:
            return value
        url = urlsplit(value)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.fragment:
            raise ValueError("Source URLs must be credential-free canonical HTTPS URLs.")
        return value


class SourceRecord(Contract):
    document_id: str
    source_id: str
    record_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    document_type: str = Field(min_length=1, max_length=100)
    canonical_url: str | None
    published_at: datetime | None
    modified_at: datetime | None
    retrieved_at: datetime
    version: str
    content_hash: str
    artifact_hash: str
    licensing_notes: str
    trust: Literal["official_snapshot", "synthetic_fixture", "private_upload"]
    scope: Literal["public", "private"]
    owner_id: StrictInt | None = None
    state: Literal["active", "withdrawn", "deleted"] = "active"
    identifiers: tuple[tuple[str, str], ...] = ()
    sections: tuple[Section, ...]

    @field_validator("published_at", "modified_at", "retrieved_at")
    @classmethod
    def aware_timestamp(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError("Provenance timestamps require an explicit timezone.")
        return value

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope == "private":
            if self.trust != "private_upload" or self.owner_id is None or self.owner_id <= 0 or self.canonical_url is not None:
                raise ValueError("Private records require an owner and cannot claim public authority.")
        elif self.owner_id is not None or self.trust == "private_upload":
            raise ValueError("Public records cannot carry private ownership.")
        if self.canonical_url is not None:
            SourceDefinition.safe_url(self.canonical_url)
        if self.published_at and self.modified_at and self.modified_at < self.published_at:
            raise ValueError("Modification cannot precede publication.")
        return self


class EvidenceChunk(Contract):
    chunk_id: str
    document_id: str
    source_version: str
    section: str
    ordinal: int
    excerpt: str
    text_hash: str


class Evidence(Contract):
    citation_id: str
    chunk_id: str
    document_id: str
    source_id: str
    record_id: str
    title: str
    canonical_url: str | None
    section: str
    excerpt: str
    published_at: datetime | None
    modified_at: datetime | None
    retrieved_at: datetime
    source_version: str
    content_hash: str
    trust: Literal["official_snapshot", "synthetic_fixture", "private_upload"]
    scope: Literal["public", "private"]


class DraftClaim(Contract):
    text: str = Field(min_length=1, max_length=2000)
    citation_ids: tuple[str, ...] = Field(min_length=1, max_length=5)


class DraftAnswer(Contract):
    claims: tuple[DraftClaim, ...] = Field(min_length=1, max_length=5)


class SupportedClaim(Contract):
    claim_id: str
    text: str
    citation_ids: tuple[str, ...]
    verification: Literal["exact_excerpt"] = "exact_excerpt"


class GroundedAnswer(Contract):
    answer: str
    claims: tuple[SupportedClaim, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    abstained: bool
    reason: str | None = None
    verification_level: str = "extractive-reference-integrity-only"
