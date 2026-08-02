from sqlalchemy.orm import Session

from app.services.dashboard_service import DashboardService
from app.services.conversation_service import ConversationService
from app.services.llm.provider_factory import ProviderFactory


class DashboardAIService:

    @staticmethod
    def generate_summary(
        db: Session,
        user_id: int = 1,
    ):

        dashboard = DashboardService.get_dashboard_stats(db)

        conversations = ConversationService.list_conversations(
            db=db,
            user_id=user_id,
        )

        recent = conversations[:5]

        conversation_text = ""

        if recent:

            for chat in recent:

                conversation_text += f"- {chat.title}\n"

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