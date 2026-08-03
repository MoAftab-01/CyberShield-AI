import secrets
import string

from sqlalchemy.orm import Session

from app.database.models import User
from app.models.password_scan import PasswordScan
from app.schemas.password_schema import PasswordResponse
from app.services.llm.provider_factory import ProviderFactory
from app.utils.password_utils import (
    calculate_entropy,
    calculate_score,
    contains_lowercase,
    contains_number,
    contains_special_character,
    contains_uppercase,
    detect_dictionary_words,
    detect_patterns,
    entropy_rating,
    password_strength,
)
from app.utils.risk_engine import PasswordRiskEngine


class PasswordService:

    @staticmethod
    def analyze(
        db: Session,
        current_user: User,
        password: str,
    ) -> PasswordResponse:

        score = calculate_score(password)

        entropy = calculate_entropy(password)

        dictionary_words = detect_dictionary_words(password)

        patterns = detect_patterns(password)

        risk = PasswordRiskEngine.calculate(
            password_length=len(password),
            has_uppercase=contains_uppercase(password),
            has_lowercase=contains_lowercase(password),
            has_number=contains_number(password),
            has_special_character=contains_special_character(password),
            entropy=entropy,
            dictionary_words=dictionary_words,
            patterns=patterns,
        )

        scan = PasswordScan(
            user_id=current_user.id,
            password_strength=password_strength(score),
            entropy=int(entropy),
            score=score,
        )

        db.add(scan)
        db.commit()

        return PasswordResponse(
            password=password,
            length=len(password),
            has_uppercase=contains_uppercase(password),
            has_lowercase=contains_lowercase(password),
            has_number=contains_number(password),
            has_special_character=contains_special_character(password),
            score=score,
            strength=password_strength(score),
            entropy=entropy,
            entropy_rating=entropy_rating(entropy),
            contains_dictionary_word=len(dictionary_words) > 0,
            detected_dictionary_words=dictionary_words,
            contains_pattern=len(patterns) > 0,
            detected_patterns=patterns,
            risk_score=risk["risk_score"],
            risk_level=risk["risk_level"],
            recommendations=risk["recommendations"],
        )

    @staticmethod
    def generate(length: int = 16):

        alphabet = (
            string.ascii_letters
            + string.digits
            + "!@#$%^&*()-_=+"
        )

        while True:

            password = "".join(
                secrets.choice(alphabet)
                for _ in range(length)
            )

            if (
                any(c.isupper() for c in password)
                and any(c.islower() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*()-_=+" for c in password)
            ):
                break

        return {
            "answer": f"""
# 🔐 Suggested Strong Password

**{password}**

Length: {length}

✅ Uppercase

✅ Lowercase

✅ Numbers

✅ Special Characters

Store this password in a password manager and enable MFA wherever possible.
"""
        }

    @staticmethod
    def recommend():

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                """
You are a cybersecurity expert.

Provide concise password best practices.

Use markdown bullet points.

Maximum 8 bullets.
"""
            )
        }

    @staticmethod
    def explain(question: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
You are a cybersecurity expert.

Explain this password-related question.

Question:
{question}

Keep the explanation concise and practical.
"""
            )
        }