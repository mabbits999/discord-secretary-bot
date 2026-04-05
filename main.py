import os
import discord
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# 会話履歴を保存
conversations = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id

    # 履歴がなければ作る
    if user_id not in conversations:
        conversations[user_id] = []

    # ユーザー発言を保存
    conversations[user_id].append({
        "role": "user",
        "content": message.content
    })

    # 最新10件だけ保持
    conversations[user_id] = conversations[user_id][-10:]

    thinking_msg = await message.channel.send("考え中...")

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=conversations[user_id]
    )

    reply = response.choices[0].message.content

    # botの返答も保存
    conversations[user_id].append({
        "role": "assistant",
        "content": reply
    })

    await thinking_msg.edit(content=reply)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
