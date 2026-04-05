from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_guild_id: int | None
    llm_provider: str
    openai_api_key: str | None
    anthropic_api_key: str | None
    model_name: str
    calendar_id: str | None
    google_service_account_json: str | None
    timezone: str
    db_path: str
    knowledge_dir: str


    @staticmethod
    def from_env() -> "Settings":
        guild_raw = os.getenv("DISCORD_GUILD_ID", "").strip()
        return Settings(
            discord_token=os.getenv("DISCORD_BOT_TOKEN", ""),
            discord_guild_id=int(guild_raw) if guild_raw else None,
            llm_provider=os.getenv("LLM_PROVIDER", "openai").strip().lower(),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            model_name=os.getenv("MODEL_NAME", "gpt-4.1-mini"),
            calendar_id=os.getenv("GOOGLE_CALENDAR_ID"),
            google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"),
            timezone=os.getenv("TZ", "Asia/Tokyo"),
            db_path=os.getenv("DB_PATH", "./data/bot.db"),
            knowledge_dir=os.getenv("KNOWLEDGE_DIR", "./knowledge"),
        )


settings = Settings.from_env()
