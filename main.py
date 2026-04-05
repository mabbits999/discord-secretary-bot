import os
import json
from datetime import datetime, timedelta, timezone

import discord
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = discord.Client(intents=intents)

# ユーザーごとの会話履歴
conversations = {}


def get_google_calendar_service():
    credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    service = build("calendar", "v3", credentials=credentials)
    return service


def get_today_events():
    service = get_google_calendar_service()

    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)

    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    if not events:
        return "今日の予定はありません。"

    lines = ["今日の予定です。"]

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "無題の予定")

        if "T" in start:
            dt = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(jst)
            time_text = dt.strftime("%H:%M")
            lines.append(f"{time_text} {summary}")
        else:
            lines.append(f"終日 {summary}")

    return "\n".join(lines)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user is None:
        return

    # botへのメンションがない場合は無視
    if bot.user not in message.mentions:
        return

    user_id = message.author.id

    # メンション文字を本文から取り除く
    content = (
        message.content.replace(f"<@{bot.user.id}>", "")
        .replace(f"<@!{bot.user.id}>", "")
        .strip()
    )

    # 今日の予定を取得
    if "今日の予定" in content or "今日のスケジュール" in content:
        reply = get_today_events()
        await message.channel.send(reply)
        return

    if not content:
        await message.channel.send("質問内容を書いてください。")
        return

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append(
        {
            "role": "user",
            "content": content,
        }
    )

    # 最新10件だけ保持
    conversations[user_id] = conversations[user_id][-10:]

    thinking_msg = await message.channel.send("考え中...")

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "あなたは有能なDiscord秘書です。短く、わかりやすく、日本語で答えてください。",
            },
            *conversations[user_id],
        ],
    )

    reply = response.choices[0].message.content

    conversations[user_id].append(
        {
            "role": "assistant",
            "content": reply,
        }
    )

    await thinking_msg.edit(content=reply)


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
