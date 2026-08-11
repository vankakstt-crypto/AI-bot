import os
import asyncio
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

# =========================
# GEMINI
# =========================

gemini = genai.Client(
    api_key=GEMINI_API_KEY
)

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# Guild -> user đang điều khiển bot
follow_users = {}


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"🤖 Bot online: {bot.user}")


# =========================
# GEMINI
# =========================

async def ask_ai(question):

    try:
        response = await asyncio.to_thread(
            gemini.models.generate_content,
            model="gemini-3.6-flash",
            contents=question
        )

        return response.text

    except Exception as e:

        print("Gemini error:", e)

        return "❌ Gemini đang gặp lỗi."


# =========================
# !JOIN
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def join(ctx):

    # Kiểm tra người dùng đang ở voice
    if not ctx.author.voice:

        await ctx.reply(
            "❌ Bạn phải vào voice room trước."
        )

        return

    channel = ctx.author.voice.channel

    voice = discord.utils.get(
        bot.voice_clients,
        guild=ctx.guild
    )

    try:

        if voice:

            await voice.move_to(channel)

        else:

            await channel.connect(
                reconnect=True
            )

        await ctx.reply(
            f"🎙️ Đã vào **{channel.name}**."
        )

        print(
            f"🎙️ Joined: {channel.name}"
        )

    except Exception as e:

        print("Join error:", e)

        await ctx.reply(
            "❌ Không thể vào voice room."
        )


# =========================
# !LEAVE
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def leave(ctx):

    voice = discord.utils.get(
        bot.voice_clients,
        guild=ctx.guild
    )

    if voice:

        await voice.disconnect(
            force=True
        )

        await ctx.reply(
            "👋 Bot đã rời room."
        )

    else:

        await ctx.reply(
            "❌ Bot không ở trong room."
        )


# =========================
# !FOLLOW
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def follow(ctx):

    if not ctx.author.voice:

        await ctx.reply(
            "❌ Bạn phải vào voice room trước."
        )

        return

    follow_users[ctx.guild.id] = ctx.author.id

    channel = ctx.author.voice.channel

    voice = discord.utils.get(
        bot.voice_clients,
        guild=ctx.guild
    )

    try:

        if voice:

            await voice.move_to(channel)

        else:

            await channel.connect(
                reconnect=True
            )

        await ctx.reply(
            f"👣 Bot đang theo bạn ở **{channel.name}**."
        )

    except Exception as e:

        print("Follow error:", e)

        await ctx.reply(
            "❌ Không thể vào room."
        )


# =========================
# !UNFOLLOW
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def unfollow(ctx):

    if ctx.guild.id in follow_users:

        del follow_users[ctx.guild.id]

        await ctx.reply(
            "🛑 Bot đã ngừng theo bạn."
        )

    else:

        await ctx.reply(
            "❌ Bot hiện không theo ai."
        )


# =========================
# TỰ ĐI THEO USER
# =========================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    # Nếu người đang được follow
    if member.id not in follow_users.values():
        return

    guild_id = member.guild.id

    if follow_users.get(guild_id) != member.id:
        return

    # User chuyển room
    if after.channel:

        voice = discord.utils.get(
            bot.voice_clients,
            guild=member.guild
        )

        if voice:

            if voice.channel != after.channel:

                try:

                    await voice.move_to(
                        after.channel
                    )

                    print(
                        f"👣 Follow → {after.channel.name}"
                    )

                except Exception as e:

                    print(
                        "Move error:",
                        e
                    )

        else:

            try:

                await after.channel.connect(
                    reconnect=True
                )

                print(
                    f"🎙️ Follow → {after.channel.name}"
                )

            except Exception as e:

                print(
                    "Connect error:",
                    e
                )


# =========================
# AI COMMAND
# =========================

@bot.command()
async def ai(ctx, *, question=None):

    if not question:

        await ctx.reply(
            "🤖 Ví dụ: `!ai Python là gì?`"
        )

        return

    async with ctx.typing():

        answer = await ask_ai(question)

    if len(answer) <= 2000:

        await ctx.reply(answer)

    else:

        for i in range(
            0,
            len(answer),
            2000
        ):

            await ctx.send(
                answer[i:i + 2000]
            )


# =========================
# MENTION = AI
# =========================

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    if bot.user in message.mentions:

        question = message.content

        question = question.replace(
            f"<@{bot.user.id}>",
            ""
        )

        question = question.replace(
            f"<@!{bot.user.id}>",
            ""
        )

        question = question.strip()

        if not question:

            await message.reply(
                "👋 Bạn muốn hỏi gì?"
            )

            return

        async with message.channel.typing():

            answer = await ask_ai(question)

        if len(answer) <= 2000:

            await message.reply(answer)

        else:

            for i in range(
                0,
                len(answer),
                2000
            ):

                await message.channel.send(
    answer[i:i + 2000]
      )
                )

    await bot.process_commands(message)


# =========================
# START
# =========================

print("🚀 Starting bot...")

bot.run(DISCORD_TOKEN)
