import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
import re
import string
import logging
import constants

from features.fortnite_fetch import start_daily_shop_task
from features.water_check import setup as setup_water_check
from features.dice_roller import roll as dice_roll_command
from features.familyguy_cutaway import search_youtube_video
from features.quote_puller import get_random_quote
from features.image_puller import pull_image, image_autocomplete
from features.dictionary import get_definition

from dotenv import load_dotenv # type: ignore
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(intents=intents,
                   command_prefix="/",
                   allowed = discord.AllowedMentions.all()
)

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

KEYWORD_RESPONSES = {
    "69" : "Nice",
    "yea man" : "City in africa",
    "yeah man" : "City in africa",
    "sclimbos" : "i'll be on",
    "Any gamers" : "i'll be on",
    "Hear me out" : ":ear:",
    "dr pepper" : "fuck you",
    "ICE" : "fuck ice",
    "trump" : "fuck trump",
    "sometimes a man gets sad" : "on god",
    "creeper" : "Aww man",
    "cnat" : "*cannot",
    "cnan" : "*can"
}

RARE_RESPONSES = [
    "I'm saying!",
    "You're not crazy for that",
    "On god",
    "Could be the move",
    "Hell yeah!",
    "man door hand hook car door",
    "idk man, you do you",
    "I don't know that I'd go that far",
    "I gotta be real...that's gas :fire:",
    "Shake the haters off like a dog do when it's wet",
    "Sometimes a man gets sad",
    "Lmfaooooo",
    "I'm gonna go nap",
    "Including or not including gang violence?",
    ":smiling_imp:",
    "Google, show me this guy's $last_word"
]

# on startup
@bot.event
async def on_ready():
    logging.info(f"Bot ready: {bot.user}")
    # Sync command tree
    try:
        await bot.tree.sync()
        logging.info("Command tree synced successfully")
    except Exception as e:
        logging.error(f"Failed to sync command tree: {e}")
    # Start background tasks
    start_daily_shop_task(bot)
    await setup_water_check(bot)

# on message
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # grab last word of message
    last_word = message.content.split()[-1] if message.content.split() else ""

    # normalize message
    def normalize(message):
        translator = str.maketrans('', '', string.punctuation)
        msg = message.lower().translate(translator)
        return msg
    
    content = normalize(message.content)

    # "chat can i get a " handler anywhere in the message
    triggers = ["tylerbot can i get a ", "tbot can i get a "]
    for trigger in triggers:
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
        rest = '"family guy" ' + rest  # prepend "family guy" to the search
        if rest:
            logger.info(f"Searching YouTube for: {rest}")
            video_url = await search_youtube_video(rest)
            if video_url:
                await message.reply(video_url, mention_author=False)
            else:
                await message.reply("Yeah idk man, I got nothing for that.", mention_author=False)
            return
        
    # "tbot define _" handler for Dictionary search
    triggers = ["tylerbot define ", "tbot define "]
    for trigger in triggers:
        idx = content.find(trigger)
        if idx != -1:
            rest = message.content[idx + len(trigger):].strip()
            if rest:
                definition = await get_definition(rest)
                await message.reply(definition, mention_author=False)
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
        if "$last_word" in response:
            response = response.replace("$last_word", last_word)
        await message.reply(response, mention_author=False)
        return


# on command
@bot.tree.command(name="watercheck", description="Send a water check message to the watercheck role")
async def watercheck(interaction: discord.Interaction):
    await interaction.response.defer()
    watercheck_role = constants.WATERCHECK_ROLE_ID
    role_mention = f"<@&{watercheck_role}>"
    message = await interaction.channel.send(f"Hey {role_mention}, water check!")
    await message.add_reaction('💧')
    
    # Update the cog's water_check_message so reactions are tracked
    water_check_cog = interaction.client.get_cog("WaterCheck")
    if water_check_cog:
        water_check_cog.water_check_message = message
    
    await interaction.followup.send("Water check message sent!", ephemeral=True)

@bot.tree.command(name="feet", description="Noah's favorite thing!")
async def feet(interaction: discord.Interaction):
    await interaction.response.send_message("Noah likes feet!")

@bot.tree.command(name="roll", description="Roll dice with the format: NdX (e.g., 2d20)")
@app_commands.describe(dice="Dice notation (e.g., 2d20, 1d100)")
async def roll(interaction: discord.Interaction, dice: str):
    await dice_roll_command(interaction, dice)

@bot.tree.command(name="quote", description="Get a random quote (admin only)")
async def quote(interaction: discord.Interaction):
    if interaction.user.id not in constants.ADMIN_USER_IDS:
        await interaction.response.send_message("Sorry dude, this one's ferda.", ephemeral=True)
        return
    await get_random_quote(interaction, constants.QUOTE_CHANNEL)

@bot.tree.command(name="8ball", description="Ask the magic 8 ball a question") 
@app_commands.describe(question="Your question for the magic 8 ball")
async def eight_ball(interaction: discord.Interaction, question: str):
    response = random.choice(RARE_RESPONSES)
    if "$last_word" in response:
        last_word = question.split()[-1] if question.split() else ""
        response = response.replace("$last_word", last_word)
    await interaction.response.send_message(f"❓ {question}\n🎱 {response}")

@bot.tree.command(name="image", description="Select or randomly pull an image from the images folder")
@app_commands.describe(image_name="Image filename or 'random' for a random image")
@app_commands.autocomplete(image_name=image_autocomplete)
async def image(interaction: discord.Interaction, image_name: str = None):
    await pull_image(interaction, image_name)


bot.run(constants.DISCORD_TOKEN)
