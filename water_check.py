import random
import datetime
import logging
import asyncio
import discord
import os
import constants
from discord.ext import tasks

logger = logging.getLogger("WaterCheck")

# Allowed window: 8:00 AM EST to midnight EST
# compensate for UTC offset
START_HOUR = 8
END_HOUR = 23  # last possible hour for reminder

channel = constants.GENERAL_CHANNEL

async def send_water_check_to_guilds(bot):
    allowed = discord.AllowedMentions(everyone=True)
    if channel:
        try:
            watercheck_role = constants.GAMERS_ROLE_ID
            role_mention = f"<@&{watercheck_role}>"
            await channel.send(f"Hey {role_mention} water check!", allowed_mentions=allowed)
            logger.info(f"Sent water check!")
        except Exception as e:
            logger.warning(f"Failed to send water check: {e}")
    else:
        logger.warning("No channel found for water check.")

def start_daily_water_check_task(bot):
    async def water_loop():
        await bot.wait_until_ready()
        logger.info("Water check task started")

        while not bot.is_closed():
            now = datetime.datetime.now()
            
            # Pick a random hour and minute between START_HOUR and END_HOUR
            rand_hour = random.randint(START_HOUR, END_HOUR)
            rand_minute = random.randint(0, 59)
            rand_second = random.randint(0, 59)
            target = now.replace(hour=rand_hour, minute=rand_minute, second=rand_second, microsecond=0)

            # If the target time already passed today, schedule for tomorrow
            if target <= now:
                target += datetime.timedelta(days=1)

            delay = (target - now).total_seconds()
            logger.info(f"Next reminder scheduled for {target} ({int(delay)}s from now)")

            await asyncio.sleep(delay)
            await send_water_check_to_guilds(bot)

    # Start the loop as a background task
    asyncio.create_task(water_loop())
