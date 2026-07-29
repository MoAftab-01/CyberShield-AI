import math
import re

SPECIAL_CHARACTERS = r"!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~"

COMMON_PASSWORD_WORDS = {
    "password",
    "admin",
    "welcome",
    "login",
    "qwerty",
    "football",
    "letmein",
    "abc123",
    "iloveyou",
    "monkey",
}


def contains_uppercase(password: str) -> bool:
    return any(char.isupper() for char in password)


def contains_lowercase(password: str) -> bool:
    return any(char.islower() for char in password)


def contains_number(password: str) -> bool:
    return any(char.isdigit() for char in password)


def contains_special_character(password: str) -> bool:
    return bool(
        re.search(
            f"[{re.escape(SPECIAL_CHARACTERS)}]",
            password,
        )
    )


def calculate_score(password: str) -> int:
    score = 0

    if len(password) >= 8:
        score += 1

    if contains_uppercase(password):
        score += 1

    if contains_lowercase(password):
        score += 1

    if contains_number(password):
        score += 1

    if contains_special_character(password):
        score += 1

    return score


def password_strength(score: int) -> str:
    if score <= 2:
        return "Weak"

    if score == 3:
        return "Moderate"

    if score == 4:
        return "Strong"

    return "Very Strong"


def character_pool(password: str) -> int:
    pool = 0

    if contains_lowercase(password):
        pool += 26

    if contains_uppercase(password):
        pool += 26

    if contains_number(password):
        pool += 10

    if contains_special_character(password):
        pool += 32

    return max(pool, 1)


def calculate_entropy(password: str) -> float:
    pool = character_pool(password)
    entropy = len(password) * math.log2(pool)
    return round(entropy, 2)


def entropy_rating(entropy: float) -> str:
    if entropy < 28:
        return "Very Weak"

    if entropy < 36:
        return "Weak"

    if entropy < 60:
        return "Moderate"

    if entropy < 80:
        return "Strong"

    return "Very Strong"

def detect_dictionary_words(password: str) -> list[str]:
    password_lower = password.lower()

    detected = []

    for word in COMMON_PASSWORD_WORDS:
        if word in password_lower:
            detected.append(word)

    return detected

KEYBOARD_PATTERNS = [
    "qwerty",
    "asdfgh",
    "zxcvbn",
]

NUMBER_PATTERNS = [
    "123456",
    "234567",
    "345678",
    "456789",
    "987654",
    "876543",
    "765432",
]

LETTER_PATTERNS = [
    "abcdef",
    "bcdefg",
    "cdefgh",
    "uvwxyz",
]

def detect_repeated_characters(password: str) -> bool:
    return len(set(password)) == 1


def detect_patterns(password: str) -> list[str]:

    password_lower = password.lower()

    patterns = []

    for pattern in KEYBOARD_PATTERNS:
        if pattern in password_lower:
            patterns.append(f"Keyboard Pattern ({pattern})")

    for pattern in NUMBER_PATTERNS:
        if pattern in password_lower:
            patterns.append(f"Sequential Numbers ({pattern})")

    for pattern in LETTER_PATTERNS:
        if pattern in password_lower:
            patterns.append(f"Sequential Letters ({pattern})")

    if detect_repeated_characters(password):
        patterns.append("Repeated Characters")

    return patterns