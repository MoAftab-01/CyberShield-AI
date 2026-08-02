from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent

from app.database.user_crud import UserCRUD

from app.services.password_service import PasswordService


class PasswordAgent(BaseAgent):

    def handle(
        self,
        question: str,
        db: Session,
        user_id: int,
        **kwargs,
    ):

        user = UserCRUD.get_by_id(
            db,
            user_id,
        )

        if not user:

            return {
                "message": "User not found."
            }

        return PasswordService.analyze(
            db=db,
            current_user=user,
            password=question,
        )