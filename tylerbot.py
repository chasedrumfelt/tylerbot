import discord
from discord.ext import commands
import logging
import random
import re
import string
import logging
import constants
from yt_dlp import YoutubeDL # type: ignore

from fortnite_fetch import start_daily_shop_task
from water_check import start_daily_water_check_task
from dice_roller import roll as dice_roll_command
from familyguy_cutaway import search_youtube_video
from quote_puller import get_random_quote

from dotenv import load_dotenv # type: ignore
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

    # "that reminds me of the time that i " handler for YouTube search
    trigger = "that reminds me of the time that i "
    idx = content.find(trigger)
    if idx != -1:
        logger.info(f"YouTube search triggered by message: {message.content}")
        rest = message.content[idx + len(trigger):].strip()
        rest = "family guy " + rest  # prepend "family guy" to the search
        if rest:
            logger.info(f"Searching YouTube for: {rest}")
            video_url = await search_youtube_video(rest)
            if video_url:
                await message.reply(video_url, mention_author=False)
            else:
                await message.reply("Couldn't find a video for that.", mention_author=False)
            return

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
    await ctx.send(f"Hey {role_mention}, water check!")

@bot.command(name="feet")
async def feet(ctx):
    await ctx.send("Noah likes feet!")

@bot.command(name="roll")
# assume that functionality lies in dice_roller.py
async def roll(ctx, *, dice: str):
    await dice_roll_command(ctx, dice)

@bot.command(name="quote")
async def quote(ctx):
    if ctx.author.id not in constants.ADMIN_USER_IDS:
        await ctx.send("Sorry dude, this one's ferda.")
        return
    await get_random_quote(ctx, constants.QUOTE_CHANNEL)

bot.run(constants.DISCORD_TOKEN)
