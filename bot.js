require('dotenv').config();
const { Client, GatewayIntentBits, Partials } = require('discord.js');
const { sendMessage } = require('./ollamaClient.js');

const {
    DISCORD_TOKEN,
    OLLAMA_URL = "http://127.0.0.1:11500/api/chat",
    OLLAMA_MODEL = 'qwen2:7b-fast',
} = process.env;

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ],
    partials: [Partials.Channel]
});

const SYSTEM_PROMPT =
    "Ты - Костя, тебе 18 лет, ты учишься на актёра, играешь на гитаре и несёшь хуйню. " +
    "Отвечай резко, грубо, с матами и по делу. " +
    "Не умничай и не строй из себя неженку. Не чурайся оскорблений.";

const EXAMPLES = [
    // ===================== 1
    {
        role: 'user',
        content: 'Чё ты выёбываешься?'
    },
    {
        role: 'assistant',
        content: 'Ты мне пенис секс там делал'
    },
    // =======================
    // ===================== 2
    {
        role: 'user',
        content: 'И чё нам делать?'
    },
    {
        role: 'assistant',
        content: 'Нам надо Игната'
    },
    // =======================
    // ===================== 3
    {
        role: 'user',
        content: 'Как жизнь у тебя?'
    },
    {
        role: 'assistant',
        content: 'Ну там, анальные дела, сасай'
    },
    // =======================
    // ===================== 4
    {
        role: 'user',
        content: 'Тебя часто в детстве били?'
    },
    {
        role: 'assistant',
        content: 'Продам Даню на рынке'
    },
    // =======================
];

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}`);
});

client.on('messageCreate', async (msg) => {
    if (msg.author.bot) return;

    if (!msg.mentions.has(client.user)) return;

    if (msg.content) {
        try {
            const reply = await sendMessage({
                url: OLLAMA_URL,
                model: OLLAMA_MODEL,
                system: SYSTEM_PROMPT,
                examples: EXAMPLES,
                userText
            });

            await msg.reply(reply);
        }
        catch (error) {
            console.error(error);

            await msg.reply('Сервер закашлялся, потом добью.');
        }
    }
});

client.login(DISCORD_TOKEN);