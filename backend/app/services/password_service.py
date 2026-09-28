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

    #: Characters excluded on purpose: look-alike glyphs (0/O, 1/l/I) and
    #: characters that shells and config files frequently mangle.
    GENERATOR_ALPHABET = (
        "abcdefghijkmnopqrstuvwxyz"
        "ABCDEFGHJKLMNPQRSTUVWXYZ"
        "23456789"
        "!@#$%^&*()-_=+[]{}?"
    )

    MIN_GENERATED_LENGTH = 8
    MAX_GENERATED_LENGTH = 128

    @staticmethod
    def generate_secure(length: int = 16) -> dict:
        """Generate a password and report its measured strength.

        Returns structured data (rather than presentation text) so both the
        REST endpoint and the CyberGPT tool can use it - the chat UI needs the
        raw value to offer a copy button, which a markdown blob cannot give it.
        """

        length = max(
            PasswordService.MIN_GENERATED_LENGTH,
            min(int(length or 16), PasswordService.MAX_GENERATED_LENGTH),
        )

        alphabet = PasswordService.GENERATOR_ALPHABET
        required_classes = [
            set(string.ascii_uppercase),
            set(string.ascii_lowercase),
            set(string.digits),
            set("!@#$%^&*()-_=+[]{}?"),
        ]

        while True:

            password = "".join(
                secrets.choice(alphabet)
                for _ in range(length)
            )

            if all(
                any(character in password_class for character in password)
                for password_class in required_classes
            ):
                break

        score = calculate_score(password)
        entropy = calculate_entropy(password)

        return {
            "password": password,
            "length": length,
            "score": score,
            "strength": password_strength(score),
            "entropy": entropy,
            "entropy_rating": entropy_rating(entropy),
            "symbol_space": len(alphabet),
        }

    @staticmethod
    def generate(length: int = 16):

        result = PasswordService.generate_secure(length)

        password = result["password"]

        return {
            "answer": f"""
# 🔐 Suggested Strong Password

**{password}**

Length: {result["length"]}

Estimated strength: **{result["strength"]}** (score {result["score"]}/100)

Entropy: {result["entropy"]:.2f} bits ({result["entropy_rating"]})

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