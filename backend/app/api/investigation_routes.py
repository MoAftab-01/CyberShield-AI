"""Authenticated, non-persisting CVE investigation endpoints."""
import json
from threading import BoundedSemaphore

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agents.cve_input import validate_cve
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.database.models import User
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/investigations", tags=["CVE Investigation"])
LIMITER = RateLimiter(6, 60)
SLOTS = BoundedSemaphore(2)


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    cve: str = Field(max_length=28)

    @field_validator("cve")
    @classmethod
    def valid_identifier(cls, value):
        return validate_cve(value)


def investigator():
    from app.agents.investigation import CVEInvestigator
    from app.agents.investigation_intelligence import OfflineIntelligence, ReadOnlyLiveIntelligence
    # Only operator-controlled settings select adapters. Never request fields.
    adapter = (ReadOnlyLiveIntelligence(approved=True)
               if settings.CVE_INVESTIGATION_LIVE_APPROVED else OfflineIntelligence())
    return CVEInvestigator(adapter)


@router.post("/cve")
def investigate(request: InvestigationRequest, stream: bool = Query(False),
                user: User = Depends(get_current_user)):
    if not settings.CVE_INVESTIGATION_ENABLED:
        raise HTTPException(503, "CVE investigation is disabled by the server operator.")
    allowed, retry = LIMITER.check(str(user.id))
    if not allowed:
        raise HTTPException(429, "Investigation rate limit exceeded.",
                            headers={"Retry-After": str(max(1, int(retry) + 1))})
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(503, "Investigation capacity is busy. Try again later.")
    try:
        agent = investigator()
        events = agent.stream(request.cve, user.id)
    except Exception:
        SLOTS.release()
        raise HTTPException(503, "Investigation initialization unavailable.") from None

    def generate():
        try:
            for event in events:
                yield json.dumps(event, separators=(",", ":")) + "\n"
        except Exception:
            yield json.dumps({"type": "error", "message": "Investigation could not complete."}) + "\n"
        finally:
            events.close()
            SLOTS.release()
    if stream:
        return StreamingResponse(generate(), media_type="application/x-ndjson",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
    try:
        report = next(event["report"] for event in events if event["type"] == "report")
        return report
    except Exception:
        raise HTTPException(503, "Investigation could not complete.") from None
    finally:
        events.close()
        SLOTS.release()
