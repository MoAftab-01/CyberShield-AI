from pydantic import BaseModel


class MitreTechnique(BaseModel):

    technique_id: str | None = None

    name: str | None = None

    description: str | None = None

    tactic: str | None = None