"""Print the resolved configuration.

A diagnostic script, so it prints what the application actually loaded rather
than what ``.env`` appears to say. It deliberately does **not** print
``JWT_SECRET``: this is the file people paste into a bug report or a chat
message, and the signing secret is the one value here whose disclosure lets
someone mint a valid token for any account. Its length and presence are enough
to diagnose a misconfiguration.
"""

from app.core.config import MIN_JWT_SECRET_LENGTH, settings

print("Application :", settings.APP_NAME)
print("Version     :", settings.APP_VERSION)
print("Database    :", settings.DATABASE_URL)
print(
    "JWT Secret  :",
    f"<set, {len(settings.JWT_SECRET)} characters>"
    if settings.JWT_SECRET
    else "<NOT SET>",
)
if len(settings.JWT_SECRET or "") < MIN_JWT_SECRET_LENGTH:
    print(
        "              ^ shorter than the recommended "
        f"{MIN_JWT_SECRET_LENGTH} characters - rotate it."
    )
print("Algorithm   :", settings.JWT_ALGORITHM)
print("Expiry      :", settings.ACCESS_TOKEN_EXPIRE_MINUTES)