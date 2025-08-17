require('dotenv').config();
const Eris = require('eris');
const bot = new Eris(process.env.DISCORD_TOKEN);
bot.on('ready', () => { console.log('READY ERIS'); process.exit(0); });
bot.on('error', console.error);
bot.connect();