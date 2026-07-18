"""Discovery service — AI-driven requirements gathering.

The AI asks essential questions about the project and stores structured requirements.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectRequirement


# The discovery questions the AI will ask
DISCOVERY_QUESTIONS = [
    {
        "key": "target_users",
        "question": "Who are the target users of this application?",
        "hint": "e.g., small business owners, enterprise employees, general public",
    },
    {
        "key": "platforms",
        "question": "What platforms should the app support?",
        "options": ["Web", "Mobile (Android)", "Mobile (iOS)", "Desktop"],
        "multiple": True,
    },
    {
        "key": "countries",
        "question": "Which countries will this app be used in?",
        "hint": "e.g., India, United States, Global",
    },
    {
        "key": "languages",
        "question": "What languages should the app support?",
        "hint": "e.g., English, Hindi, Spanish",
    },
    {
        "key": "auth_type",
        "question": "What authentication method do you need?",
        "options": ["Email & Password", "Social Login (Google/GitHub)", "Phone OTP", "SSO / SAML", "None yet"],
        "multiple": False,
    },
    {
        "key": "payment_providers",
        "question": "Do you need payment integration? If so, which providers?",
        "options": ["Stripe", "Razorpay", "PayPal", "None"],
        "multiple": True,
    },
    {
        "key": "integrations",
        "question": "What third-party integrations do you need?",
        "hint": "e.g., SendGrid, Twilio, Slack, Google Maps, WhatsApp",
    },
    {
        "key": "branding",
        "question": "Do you have branding requirements (colors, logo, domain)?",
        "hint": "e.g., primary color #1A73E8, logo URL, custom domain",
    },
]


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_questions(self) -> list[dict]:
        """Return the discovery questions."""
        return DISCOVERY_QUESTIONS

    async def get_requirements(self, project_id: str) -> ProjectRequirement | None:
        """Get existing requirements for a project."""
        result = await self.db.execute(
            select(ProjectRequirement).where(ProjectRequirement.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def save_requirements(
        self,
        project_id: str,
        target_users: str | None = None,
        platforms: list | None = None,
        countries: list | None = None,
        languages: list | None = None,
        auth_type: str | None = None,
        payment_providers: list | None = None,
        integrations: list | None = None,
        branding: dict | None = None,
    ) -> ProjectRequirement:
        """Save or update requirements for a project."""
        existing = await self.get_requirements(project_id)

        if existing:
            if target_users is not None:
                existing.target_users = target_users
            if platforms is not None:
                existing.platforms = platforms
            if countries is not None:
                existing.countries = countries
            if languages is not None:
                existing.languages = languages
            if auth_type is not None:
                existing.auth_type = auth_type
            if payment_providers is not None:
                existing.payment_providers = payment_providers
            if integrations is not None:
                existing.integrations = integrations
            if branding is not None:
                existing.branding = branding
            await self.db.flush()
            return existing

        requirements = ProjectRequirement(
            project_id=project_id,
            target_users=target_users,
            platforms=platforms or [],
            countries=countries or [],
            languages=languages or [],
            auth_type=auth_type,
            payment_providers=payment_providers or [],
            integrations=integrations or [],
            branding=branding or {},
        )
        self.db.add(requirements)
        await self.db.flush()

        # Update project status
        await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project and project.status == "draft":
            project.status = "discovering"

        await self.db.flush()
        return requirements
