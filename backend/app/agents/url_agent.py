from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent

from app.database.user_crud import UserCRUD

from app.services.url_service import URLService


class URLAgent(BaseAgent):

    async def handle(
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

        return await URLService.analyze(
            db=db,
            current_user=user,
            url=question,
        )