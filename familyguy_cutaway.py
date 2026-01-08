# familyguy_cutaway.py - provide as a Cog to be loaded by your main bot
# Requires: discord.py, youtubesearchpython
# pip install discord.py youtubesearchpython

import asyncio
import discord
from discord.ext import commands

try:
    from youtubesearchpython import VideosSearch
except Exception:
    VideosSearch = None  # handle missing dependency at runtime

class FamilyGuyCutaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='yt', help='Search YouTube and return the top result link. Usage: !yt your search terms')
    async def yt(self, ctx, *, query: str):
        if VideosSearch is None:
            await ctx.send("Missing dependency 'youtubesearchpython'. Install with: pip install youtubesearchpython")
            return
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: VideosSearch(query, limit=1).result())
        try:
            link = result['result'][0]['link']
            await ctx.send(link)
        except (KeyError, IndexError):
            await ctx.send("No results found.")

def setup(bot: commands.Bot):
    """For discord.py < 2.0 (sync extensions loader)."""
    bot.add_cog(FamilyGuyCutaway(bot))

# If you're using discord.py 2.0+ and the async loader pattern, use this loader instead:
# async def setup(bot: commands.Bot):
#     await bot.add_cog(FamilyGuyCutaway(bot))