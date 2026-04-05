import os
import discord
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = discord.Client(intents=intents)

# ユーザーごとの会話履歴
conversations = {}

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
    content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

    if not content:
        await message.channel.send("質問内容を書いてください。")
        return

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({
        "role": "user",
        "content": content
    })

    # 最新10件だけ保持
    conversations[user_id] = conversations[user_id][-10:]

    thinking_msg = await message.channel.send("考え中...")

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "あなたは有能なDiscord秘書です。短く、わかりやすく、日本語で答えてください。"
            },
            *conversations[user_id]
        ]
    )

    reply = response.choices[0].message.content

    conversations[user_id].append({
        "role": "assistant",
        "content": reply
    })

    await thinking_msg.edit(content=reply)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
