from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .calendar_service import create_calendar_event
from .config import settings
from .db import get_conn, init_db
from .knowledge import search_knowledge
from .llm import complete, compose_knowledge_prompt, compose_research_prompt


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


class Secretary(commands.Cog):
    def __init__(self, bot_: commands.Bot):
        self.bot = bot_
        self.reminder_loop.start()

    def cog_unload(self) -> None:
        self.reminder_loop.cancel()

    @app_commands.command(name="ask", description="秘書AIに質問する")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        answer = await asyncio.to_thread(complete, question)
        await interaction.followup.send(answer[:1900], ephemeral=True)

    @app_commands.command(name="research", description="調べ物を依頼する")
    async def research(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer(thinking=True)
        prompt = compose_research_prompt(topic)
        answer = await asyncio.to_thread(complete, prompt)
        await interaction.followup.send(f"調査テーマ: {topic}\n\n{answer[:1800]}")

    @app_commands.command(name="knowledge", description="knowledgeフォルダから答える")
    async def knowledge(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        sources = search_knowledge(question)
        if not sources:
            await interaction.followup.send("knowledge フォルダに近い資料が見つかりませんでした。", ephemeral=True)
            return
        prompt = compose_knowledge_prompt(question, sources)
        answer = await asyncio.to_thread(complete, prompt)
        source_names = "\n".join([f"・{name}" for name, _ in sources])
        await interaction.followup.send(f"{answer[:1500]}\n\n参照資料\n{source_names}", ephemeral=True)

    @app_commands.command(name="delegate", description="ワーカーに依頼を送る")
    async def delegate(
        self,
        interaction: discord.Interaction,
        worker: discord.Member,
        title: str,
        due_date: str,
        description: str,
    ):
        await interaction.response.defer(thinking=True)
        channel = interaction.channel
        requester = interaction.user.mention
        body = (
            f"{worker.mention}\n"
            f"新しい依頼です。\n\n"
            f"タイトル: {title}\n"
            f"納期: {due_date}\n"
            f"依頼者: {requester}\n"
            f"内容: {description}\n\n"
            f"対応する場合は『受付完了』、納品時は『納品完了』と返信してください。"
        )
        sent = await channel.send(body)
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO tasks(requester, worker, title, description, due_date, source_channel, source_message_link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(interaction.user),
                    str(worker),
                    title,
                    description,
                    due_date,
                    str(channel.id if channel else ""),
                    sent.jump_url,
                ),
            )
            conn.commit()
        await interaction.followup.send("依頼を送信して、DBにも記録しました。", ephemeral=True)

    @app_commands.command(name="calendar_add", description="Googleカレンダーに予定を入れる")
    async def calendar_add(
        self,
        interaction: discord.Interaction,
        title: str,
        start: str,
        end: str,
        description: Optional[str] = "",
        location: Optional[str] = "",
    ):
        await interaction.response.defer(thinking=True, ephemeral=True)
        link = await asyncio.to_thread(create_calendar_event, title, start, end, description or "", location or "")
        await interaction.followup.send(f"予定を作成しました。\n{link}", ephemeral=True)

    @app_commands.command(name="remind", description="指定時刻にチャンネルへ通知する")
    async def remind(self, interaction: discord.Interaction, remind_at: str, title: str, body: str):
        # remind_at example: 2026-04-10 20:00
        await interaction.response.defer(ephemeral=True)
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO reminders(channel_id, remind_at, title, body) VALUES (?, ?, ?, ?)",
                (str(interaction.channel_id), remind_at, title, body),
            )
            conn.commit()
        await interaction.followup.send("リマインドを登録しました。", ephemeral=True)

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        tz = ZoneInfo(settings.timezone)
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
        rows = []
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM reminders WHERE sent = 0 AND remind_at <= ? ORDER BY remind_at ASC",
                (now,),
            ).fetchall()
        for row in rows:
            channel = self.bot.get_channel(int(row["channel_id"]))
            if channel:
                await channel.send(f"【リマインド】{row['title']}\n{row['body']}")
            with get_conn() as conn:
                conn.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (row["id"],))
                conn.commit()

    @reminder_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        if settings.discord_guild_id:
            guild = discord.Object(id=settings.discord_guild_id)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Command sync error: {e}")


async def main() -> None:
    init_db()
    await bot.add_cog(Secretary(bot))
    if not settings.discord_token:
        raise RuntimeError("DISCORD_BOT_TOKEN が未設定です")
    await bot.start(settings.discord_token)
