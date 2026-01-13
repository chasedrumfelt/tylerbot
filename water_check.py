import random
import datetime
import logging
import asyncio
import discord
import os
import constants
from discord.ext import tasks, commands

logger = logging.getLogger("WaterCheck")

# Allowed window: 9a - 9p EST
# compensate for UTC offset
START_HOUR = 4
END_HOUR = 16

class WaterCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.water_check_message = None

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        if self.water_check_message and reaction.message.id == self.water_check_message.id and str(reaction.emoji) == '💧':
            role = reaction.message.guild.get_role(constants.WATERCHECK_ROLE_ID)
            if role:
                await user.add_roles(role)
                logger.info(f"Assigned {role.name} to {user}")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        if self.water_check_message and reaction.message.id == self.water_check_message.id and str(reaction.emoji) == '💧':
            role = reaction.message.guild.get_role(constants.WATERCHECK_ROLE_ID)
            if role:
                await user.remove_roles(role)
                logger.info(f"Removed {role.name} from {user}")

    async def send_water_check_to_guilds(self):
        allowed = discord.AllowedMentions(everyone=True)
        try:
            target_channel = self.bot.get_channel(constants.GENERAL_CHANNEL)
            watercheck_role = constants.WATERCHECK_ROLE_ID
            role_mention = f"<@&{watercheck_role}>"
            message = await target_channel.send(f"Hey gang, {role_mention}!", allowed_mentions=allowed)
            self.water_check_message = message
            await message.add_reaction('💧')
            logger.info(f"Sent water check!")
        except Exception as e:
            logger.warning(f"Failed to send water check: {e}")

    def start_daily_water_check_task(self):
        async def water_loop():
            await self.bot.wait_until_ready()
            logger.info("Water check task started")

            while not self.bot.is_closed():
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
                await self.send_water_check_to_guilds()

        # Start the loop as a background task
        asyncio.create_task(water_loop())

async def setup(bot):
    await bot.add_cog(WaterCheck(bot))
