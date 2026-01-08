import discord
from discord.ext import commands
import logging
import random
import re
import string
import logging
import constants
from yt_dlp import YoutubeDL

from fortnite_fetch import start_daily_shop_task
from water_check import start_daily_water_check_task
from dice_roller import roll as dice_roll_command

from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", 
                   intents=intents,
                   allowed = discord.AllowedMentions.all()
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("TylerBot")

KEYWORD_RESPONSES = {
    "69" : "Nice",
    "yea man" : "City in africa",
    "yeah man" : "City in africa",
    "sclimbos" : "i'll be on",
    "Any gamers" : "i'll be on",
    "Hear me out" : ":ear:",
    "dr pepper" : "fuck you"
}

RARE_RESPONSES = [
    "I'm saying!",
    "You're not crazy for that",
    "On god",
    "Could be the move",
    "Hell yeah!",
    "man door hand hook car door"
]

# on startup
@bot.event
async def on_ready():
    logging.info(f"Bot ready: {bot.user}")
    # Start background tasks
    start_daily_shop_task(bot)
    start_daily_water_check_task(bot)

# on message
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # normalize message
    def normalize(message):
        translator = str.maketrans('', '', string.punctuation)
        msg = message.lower().translate(translator)
        return msg
    
    content = normalize(message.content)

    # Quick "chat can i get a " handler anywhere in the message
    trigger = "chat can i get a "
    idx = content.find(trigger)
    if idx != -1:
        rest = message.content[idx + len(trigger):].strip()
        if rest:
            await message.reply(rest, mention_author=False)
            return

    # YouTube search handler for "this reminds me of the time that i "
    yt_trigger = "this reminds me of the time that i "
    yt_idx = content.find(yt_trigger)
    if yt_idx != -1:
        search_query = message.content[yt_idx + len(yt_trigger):].strip()
        if search_query:
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                    if info and 'entries' in info and len(info['entries']) > 0:
                        video_url = f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"
                        await message.reply(video_url, mention_author=False)
                        return
            except Exception as e:
                logging.error(f"Error searching YouTube: {e}")

    # Check for keyword responses
    for keyword, response in KEYWORD_RESPONSES.items():
        keyword_normalized = normalize(keyword)
        # Use regex to match whole keywords/phrases
        # \b ensures word boundaries
        pattern = rf"\b{re.escape(keyword_normalized)}\b"
        if re.search(pattern, content):
            await message.reply(response, mention_author=False)
            return

    # chance for rare responses
    if random.random() < 0.01:  # 1% chance
        response = random.choice(RARE_RESPONSES)
        await message.reply(response, mention_author=False)

    await bot.process_commands(message)


# on command
@bot.command(name="watercheck")
async def watercheck(ctx):
    watercheck_role = constants.GAMERS_ROLE_ID
    role_mention = f"<@&{watercheck_role}>"
    await ctx.send(f"Hey guys, {role_mention}")

@bot.command(name="feet")
async def feet(ctx):
    await ctx.send("Noah likes feet!")

@bot.command(name="roll")
# assume that functionality lies in dice_roller.py
async def roll(ctx, *, dice: str):
    await dice_roll_command(ctx, dice)

bot.run(constants.DISCORD_TOKEN)
