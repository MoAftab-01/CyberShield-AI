from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.agents.capability_router import CapabilityRouter

from app.database.user_crud import UserCRUD

from app.services.password_service import PasswordService


class PasswordAgent(BaseAgent):

    CAPABILITIES = [
        "analyze",
        "generate",
        "recommend",
        "explain",
    ]

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

        capability = CapabilityRouter.route(
            agent="Password Agent",
            capabilities=self.CAPABILITIES,
            question=question,
        )
        print("========== PASSWORD AGENT ==========")
        print("Question:", question)
        print("Capability:", capability)
        print("===================================")

        print(
            f"[PasswordAgent] {capability}"
        )

        if capability == "generate":

            return PasswordService.generate()

        elif capability == "recommend":

            return PasswordService.recommend()

        elif capability == "explain":

            return PasswordService.explain(
                question
            )

        return PasswordService.analyze(
            db=db,
            current_user=user,
            password=question,
        )