from app.schemas.user_schema import UserCreate

user = UserCreate(
    name="Mohammed Aftab",
    email="aftab@gmail.com",
    password="Password@123"
)

print(user)