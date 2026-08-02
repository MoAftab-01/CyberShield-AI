from sqlalchemy.orm import Session

from app.database.models import User


class UserCRUD:

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: int,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )