import os
import asyncio
from dotenv import load_dotenv
import logging
import aiohttp
from discord.ext import commands


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOCAL_INFERENCE_URL = os.getenv("LOCAL_INFERENCE_URL", "http://127.0.0.1:8000/agent/consult")
REQUEST_TIMEOUT = int(os.getenv("LOCAL_INFERENCE_TIMEOUT", "15"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bot")


intents = commands.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (id: {bot.user.id})")


@bot.event
async def on_message(message):
    # ignore messages from bots (including ourselves)
    if message.author.bot:
        return

    term = message.content.strip()
    if not term:
        return

    # optional: simple command to call local agent
    # call local inference HTTP endpoint
    try:
        async with aiohttp.ClientSession() as session:
            params = {"term": term}
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with session.get(LOCAL_INFERENCE_URL, params=params, timeout=timeout) as resp:
                if resp.status != 200:
                    text = f"문의 처리 중 오류가 발생했습니다 (상태코드 {resp.status})."
                    await message.channel.send(text)
                    logger.error("Inference endpoint returned status %s", resp.status)
                    return

                data = await resp.json()

        # Expecting response keys: 'emotion_interpretation', 'professional_response', 'analysis'
        interp = data.get("emotion_interpretation") or "(해석 없음)"
        prof = data.get("professional_response") or data.get("ai_response") or "(응답 없음)"
        tag = data.get("analysis", {}).get("final_scenario") or ""

        reply_lines = []
        if tag:
            reply_lines.append(f"[{tag}]")
        reply_lines.append(interp)
        reply_lines.append("")
        reply_lines.append(prof)

        reply_text = "\n".join(reply_lines)
        # Discord has message length limits; split if too long
        if len(reply_text) <= 1900:
            await message.channel.send(reply_text)
        else:
            # chunk into multiple messages
            for i in range(0, len(reply_text), 1800):
                await message.channel.send(reply_text[i:i+1800])

    except asyncio.TimeoutError:
        await message.channel.send("응답 시간이 초과되었습니다. 나중에 다시 시도해주세요.")
        logger.exception("Timeout calling inference service")
    except Exception as e:
        await message.channel.send("처리 중 오류가 발생했습니다.")
        logger.exception("Error handling message: %s", e)


def main():
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set in environment")
        print("Please set DISCORD_TOKEN in your .env or environment variables.")
        return

    try:
        bot.run(DISCORD_TOKEN)
    except Exception:
        logger.exception("Bot terminated with an exception")


if __name__ == '__main__':
    main()
