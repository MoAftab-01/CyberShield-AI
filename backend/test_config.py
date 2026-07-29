from app.core.config import settings

print("Application :", settings.APP_NAME)
print("Version     :", settings.APP_VERSION)
print("Database    :", settings.DATABASE_URL)
print("JWT Secret  :", settings.JWT_SECRET)
print("Algorithm   :", settings.JWT_ALGORITHM)
print("Expiry      :", settings.ACCESS_TOKEN_EXPIRE_MINUTES)