from sqlalchemy.orm import Session

from app.database.models import User

from app.services.dashboard_service import DashboardService
from app.services.conversation_service import ConversationService
from app.services.llm.provider_factory import ProviderFactory


class DashboardAIService:

    @staticmethod
    def generate_summary(
        db: Session,
        current_user: User,
    ):

        dashboard = DashboardService.get_dashboard_stats(
            db=db,
            current_user=current_user,
        )

        conversations = ConversationService.list_conversations(
            db=db,
            user_id=current_user.id,
        )

        recent = conversations[:5]

        if recent:

            conversation_text = "\n".join(
                f"- {chat.title}"
                for chat in recent
            )

        else:

            conversation_text = "No recent conversations."

        prompt = f"""
You are an Enterprise Cyber Security Assistant.

Analyze the following security dashboard.

Security Score:
{dashboard["stats"]["securityScore"]}

Passwords Checked:
{dashboard["stats"]["passwordsChecked"]}

URLs Scanned:
{dashboard["stats"]["urlsScanned"]}

Threat Searches:
{dashboard["stats"]["threatsDetected"]}

Recent Conversations:

{conversation_text}

Generate:

1. Executive Summary

2. Key Risks

3. Recommendations

Keep the response under 200 words.

Respond in markdown.
"""

        provider = ProviderFactory.get_provider()

        summary = provider.chat(prompt)

        return {
            "summary": summary
        }