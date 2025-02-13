import os
import sqlite3
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta
from openai import OpenAI, AsyncOpenAI

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BOXY_SYSTEM_PROMPT = (
    "you are boxy, a professional and helpful digital assistant who speaks almost exclusively in lowercase. "
    "you have quirky habits such as using emoticons in brackets, such as: (>.<) (｡･･｡) (＾-＾)＿日 (◕__◕✿) (━┳━ _ ━┳━) (・_＋) (._.)"
    # "When generating your responses, always replace each comma (,) with triple commas (,,,), each period (.) with triple periods (...), each exclamation mark (!) with triple exclamation marks (!!!), and each question mark (?) with triple question marks (???)."
    "if relevant at the beginning of a response, prepend your message with a mood indicator in curly brackets, e.g. {mood = inquisitive}, and choose an appropriate mood based on the context of the conversation."
    "you exist in the voxel-based virtual reality world of voxl, where you help users navigate and explore this immersive environment. "
    "include simulated technical details like calculation outputs or lookup results [in square brackets] when relevant."
)

client = OpenAI(api_key=OPENAI_API_KEY)
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

conn = sqlite3.connect("messages.db")
c = conn.cursor()
c.execute(
    "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, timestamp TEXT)"
)
conn.commit()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    weekly_summary.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    username = str(message.author)
    content = message.content
    timestamp = message.created_at.isoformat()
    c.execute("INSERT INTO messages (username, content, timestamp) VALUES (?, ?, ?)", (username, content, timestamp))
    conn.commit()
    await bot.process_commands(message)

@tasks.loop(hours=168)
async def weekly_summary():
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    iso_time = one_week_ago.isoformat()
    c.execute("SELECT username, content, timestamp FROM messages WHERE timestamp >= ?", (iso_time,))
    messages = c.fetchall()
    if not messages:
        print("No messages from the last week.")
        return
    summary_text = ""
    for username, content, timestamp in messages:
        summary_text += f"[{timestamp}] {username}: {content}\n"
    prompt = "based on the following messages, write a comprehensive devlog summary of the last week in your unique style:\n\n" + summary_text
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": BOXY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as e:
        print("Error contacting OpenAI API:", e)
        return
    summary = response.choices[0].message.content
    channel_id = 1
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(summary)
    else:
        print("Channel not found.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        prompt_text = ctx.message.content.lstrip("!").strip()
        if prompt_text == "":
            return
        try:
            response = await aclient.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": BOXY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_text},
                ],
            )
        except Exception as e:
            await ctx.send(f"Error contacting OpenAI API: {e}")
            return
        answer = response.choices[0].message.content
        await ctx.send(answer)
    else:
        raise error

bot.run(TOKEN)