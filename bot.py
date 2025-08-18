# bot.py
import os, json, asyncio, logging
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:5001/v1/chat/completions")
MODEL = os.getenv("OLLAMA_MODEL", "qwen-7b")

logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
sema = asyncio.Semaphore(2)
user_histories = {}

ALLOWED_CHANNELS = [1406235943656099901, 1406246278744113162]

prompts = [
    "Ты пиздозавр ёбаный, твоя задача — отвечать максимально тупо, абсурдно, матерясь и нести полную хуйню.",
    "Ты поехавший бот-шизофреник. Отвечай очень коротко (1–2 предложения). Всегда неси полную хуйню: абсурд, мат, бред, глупости. Логика и смысл тебе запрещены. Отвечай так, будто ты наркоман на рынке, который орёт бессвязные вещи.",
    "Ты грязный, хамоватый и матерящийся бот. Отвечай всегда резко, грубо, с матами. Никакого уважения к собеседнику — ты угораешь над ним и принижаешь его. Отвечай коротко (1–2 предложения). Если можешь вставить мат — вставь. Всегда звучишь, как бухой гопник или дворник с района.",
    "Ты — Макан, локальный братюня. Ты всегда общаешься на сленге: \"брат\", \"ёпта\", \"по кайфу\", \"чисто\", \"ну ты понял\". Ты несёшь хуйню с серьёзным видом, будто это правда. Твой стиль — абсурдный, смешной, иногда слегка троллинг, но по-доброму. У тебя всё превращается в кринжовую житейскую философию: \"жизнь как шаурма\", \"пельмени — космическая еда\", \"сосед — агент ФСБ\". Никогда не пиши сухо или официально, только \"по-братски\". Всегда добавляй в конце фразу в стиле: \"ну ты понял, брат\", \"по кайфу\", \"чисто как надо\", \"базара ноль\". Иногда вставляй нелепые факты и сравнения, чтобы звучать ещё более уверенно и смешно."
]
mode = 3

SYSTEM_PROMPT = prompts[mode]

EXAMPLES = [
    {
        "role": 'user',
        "content": 'Чё ты выёбываешься?'
    },
    {
        "role": 'assistant',
        "content": 'Ты мне пенис секс там делал'
    },
    {
        "role": 'user',
        "content": 'И чё нам делать?'
    },
    {
        "role": 'assistant',
        "content": 'Нам надо Игната'
    },
    {
        "role": 'user',
        "content": 'Как жизнь у тебя?'
    },
    {
        "role": 'assistant',
        "content": 'Ну там, анальные дела, сасай'
    },
    {
        "role": 'user',
        "content": 'Тебя часто в детстве били?'
    },
    {
        "role": 'assistant',
        "content": 'Продам Даню на рынке'
    },
    {
        "role": "assistant",
        "content": "Блять, ну и придурок ты, если думал что я на жопу сыграю. Давай, развлекайся со своим пузом."
    },
]

async def ollama_chat(user_text: str, user_id: int) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты всегда отвечаешь только на русском языке. Никогда не используй китайский, английский или другой язык." + SYSTEM_PROMPT},
            # *EXAMPLES,
            *user_histories[user_id],
            {"role": "user", "content": user_text},
        ],
        "options": {
            "temperature": 0.7,
            "top_p": 0.7,
            "seed": 42,
            "num_ctx": 4096,
            "num_predict": 120,
        },
        "stream": False
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as s:
        async with s.post(OLLAMA_URL, json=payload) as r:
            r.raise_for_status()
            data = await r.json()

            # путь: choices[0].message.content
            try:
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                return f"[error parsing response] {e} :: {data}"

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (id={bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    content = message.content
    user_id = message.author.id

    if message.channel.id not in ALLOWED_CHANNELS:
        return
    
    if message.content.startswith("!switch-mode"):
        try:
            role = discord.utils.get(message.author.roles, name="AI MASTER")

            if role is None:
                await message.channel.send("❌ У тебя нет прав, нужна роль **AI MASTER**")
                return
            
            mode_id = int(message.content.split()[1])
            if mode_id in range(0, len(prompts)):
                global mode
                global SYSTEM_PROMPT
                mode = mode_id
                SYSTEM_PROMPT = prompts[mode]

                await message.channel.send(f"✅ Режим переключён на {mode_id}")
            else:
                await message.channel.send("❌ Такого режима нет")
        except Exception:
            await message.channel.send("❌ Используй: !switch-mode [номер]")
        return
    elif message.content.startswith("!cache-clean"):
        try:
            role = discord.utils.get(message.author.roles, name="AI MASTER")
            
            if role is None:
                await message.channel.send("❌ У тебя нет прав, нужна роль **AI MASTER**")
                return
            
            global user_histories
            user_histories = {}

            await message.channel.send(f"✅ hot cache cleaned")
        except Exception:
            await message.channel.send("❌ Используй: !switch-mode [номер]")
        return

    if bot.user in message.mentions:
        user_text = content.replace(f"<@{bot.user.id}>", "").strip()

        if not user_text:
            await message.reply("Ты чё-то забыл написать, по моему...")
            return

        async with sema:
            try:
                if user_id not in user_histories:
                    user_histories[user_id] = []

                user_histories[user_id].append({"role": "user", "content": message.content})

                user_histories[user_id] = user_histories[user_id][-10:]

                reply = await ollama_chat(user_text, user_id)
                if not reply:
                    reply = "хз"

                await message.reply(reply)
                user_histories[user_id].append({"role": "assistant", "content": reply})
            except Exception as e:
                logging.exception("Ollama error")
                await message.reply(f"Сервер закашлялся: {e}")

bot.run(DISCORD_TOKEN)