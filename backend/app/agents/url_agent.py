from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.agents.capability_router import CapabilityRouter

from app.database.user_crud import UserCRUD

from app.services.url_service import URLService


class URLAgent(BaseAgent):

    CAPABILITIES = [
        "analyze",
        "explain",
        "recommend",
        "education",
    ]

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

        capability = CapabilityRouter.route(
            agent="URL Agent",
            capabilities=self.CAPABILITIES,
            question=question,
        )

        print(
            f"[URLAgent] {capability}"
        )

        if capability == "explain":

            return URLService.explain(
                question
            )

        elif capability == "recommend":

            return URLService.recommend()

        elif capability == "education":

            return URLService.education(
                question
            )

        return await URLService.analyze(
            db=db,
            current_user=user,
            url=question,
        )