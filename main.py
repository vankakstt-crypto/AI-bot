import os
import discord
from discord.ext import commands
from google import genai

# =========================
# CONFIG
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("Thiếu DISCORD_TOKEN")

if not GEMINI_API_KEY:
    raise RuntimeError("Thiếu GEMINI_API_KEY")

# Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot đã online: {bot.user}")
    print(f"ID: {bot.user.id}")


# =========================
# AI COMMAND
# =========================

@bot.command()
async def ai(ctx, *, question):
    """
    Dùng:
    !ai câu hỏi của bạn
    """

    await ctx.typing()

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=question
        )

        answer = response.text

        if not answer:
            answer = "Gemini không trả về nội dung."

        # Discord giới hạn message khoảng 2000 ký tự
        if len(answer) <= 2000:
            await ctx.reply(answer)
        else:
            for i in range(0, len(answer), 2000):
                await ctx.send(answer[i:i + 2000])

    except Exception as e:
        print("Lỗi Gemini:", e)
        await ctx.reply(
            "❌ Có lỗi khi kết nối với Gemini."
        )


# =========================
# AI KHI MENTION BOT
# =========================

@bot.event
async def on_message(message):

    # Không trả lời chính bot
    if message.author == bot.user:
        return

    # Nếu mention bot
    if bot.user in message.mentions:

        question = message.content

        # Xóa mention bot
        question = question.replace(
            f"<@{bot.user.id}>",
            ""
        ).replace(
            f"<@!{bot.user.id}>",
            ""
        ).strip()

        if not question:
            await message.reply(
                "👋 Bạn muốn hỏi gì?"
            )
            return

        async with message.channel.typing():

            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=question
                )

                answer = response.text

                if not answer:
                    answer = "Gemini không trả về nội dung."

                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    for i in range(0, len(answer), 2000):
                        await message.channel.send(
                            answer[i:i + 2000]
                        )

            except Exception as e:
                print("Lỗi Gemini:", e)

                await message.reply(
                    "❌ Không thể kết nối với AI."
                )

    # Cho phép các command !ai hoạt động
    await bot.process_commands(message)


# =========================
# START BOT
# =========================

bot.run(DISCORD_TOKEN)
