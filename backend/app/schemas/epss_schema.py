from pydantic import BaseModel


class EPSSSchema(BaseModel):

    epss_score: float | None = None

    epss_percentile: float | None = None

    epss_date: str | None = None