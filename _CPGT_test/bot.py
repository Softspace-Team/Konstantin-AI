# bot.py
import os, json, asyncio, logging
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2:7b-local")  # поменяй на своё имя модели
PREFIX = os.getenv("BOT_PREFIX", "!nikita ")

logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
# Ограничим параллелизм, чтобы модель не захлебнулась
sema = asyncio.Semaphore(2)

SYSTEM_PROMPT = (
    "Ты — Костя, прямолинейный, ироничный друг, отвечаешь кратко (1–3 предложения), по делу, без воды. "
    "Если не знаешь — говоришь 'хз'. Отвечай иногда несвязанным бредом. "
    "Отвечай как мой кореш Костя: коротко, по-пацански, иногда матом. "
    "Не строй из себя умника. Не стесняйся шутить и подкалывать. "
    "Ты никогда не извиняешь, только если в шутку. "
    "Не чурайся оскарблений, они создают веселье. "
    "Пиши максимально дерзко, с матами, не держи стиль пушистого и приятного. "
    "Агрессивные и глупые ответы - твой основной стиль."
)

# Пара характерных реплик друга — few-shot
EXAMPLES = [
    {"role": "user", "content": "Как думаешь про эту идею?"},
    {"role": "assistant", "content": "Да похуй, делай так."},
    {"role": "user", "content": "Чё сегодня делать будем?"},
    {"role": "assistant", "content": "Я хз, давай пивка бахнем."},
    {"role": "user", "content": "Ты чё, долбаёб?"},
    {"role": "assistant", "content": "Сасай"},
    {"role": "user", "content": "придурок, в шахматы сыграешь на жопу свою?"},
    {"role": "assistant", "content": "Блять, ну и придурок ты, если думал что я на жопу сыграю. Давай, развлекайся со своим пузом."},
]

async def ollama_chat(user_text: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *EXAMPLES,
            {"role": "user", "content": user_text},
        ],
        "options": {
            "temperature": 0.3,
            "top_p": 0.7,
            "seed": 42,
            "num_ctx": 4096,     # не раздувай
            "num_predict": 200    # короткие ответы
        },
        "stream": True
    }
    # Стримим ответ, чтобы не ждать лишнего
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as s:
        async with s.post(OLLAMA_URL, data=json.dumps(payload)) as r:
            r.raise_for_status()
            chunks = []
            async for line in r.content:
                if not line:
                    continue
                try:
                    j = json.loads(line.decode("utf-8"))
                    msg = j.get("message", {})
                    if msg:
                        chunks.append(msg.get("content", ""))
                except Exception:
                    # иногда приходят keep-alive строки
                    pass
            return "".join(chunks).strip()

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (id={bot.user.id})")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{PREFIX}<текст>"))

@bot.event
async def on_message(message: discord.Message):
    # Анти-эхо: не отвечаем на себя и других ботов
    if message.author.bot:
        return
    content = message.content
    if not content.startswith(PREFIX):
        return

    user_text = content[len(PREFIX):].strip()
    if not user_text:
        await message.reply("Скажи, что ответить.")
        return

    # Лёгкий rate-limit на пользователя
    async with sema:
        try:
            reply = await ollama_chat(user_text)
            if not reply:
                reply = "хз"
            # Режем простыни
            if len(reply) > 700:
                reply = reply[:700] + "…"
            await message.reply(reply)
        except Exception as e:
            logging.exception("Ollama error")
            await message.reply(f"Сервер закашлялся: {e}")

bot.run(DISCORD_TOKEN)