from pydantic import BaseModel, Field


class PasswordRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=256)


class PasswordResponse(BaseModel):
    password: str

    length: int

    has_uppercase: bool

    has_lowercase: bool

    has_number: bool

    has_special_character: bool

    score: int

    strength: str

    entropy: float

    entropy_rating: str

    contains_dictionary_word: bool

    detected_dictionary_words: list[str]

    contains_pattern: bool

    detected_patterns: list[str]

    risk_score: int

    risk_level: str

    recommendations: list[str]