from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.database.models import User
from app.schemas.user_schema import UserCreate


class UserService:

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:

        existing_user = (
            db.query(User)
            .filter(User.email == user.email)
            .first()
        )

        if existing_user:
            raise ValueError("Email already exists.")

        hashed_password = hash_password(user.password)

        new_user = User(
            name=user.name,
            email=user.email,
            hashed_password=hashed_password,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> User | None:

        user = UserService.get_user_by_email(
            db,
            email,
        )

        if user is None:
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        return user