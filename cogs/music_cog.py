import discord
import asyncio
from discord.ext import commands
from discord import app_commands


class MusicStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.disconnect_timer = None

    
    async def cog_unload(self):
        if self.disconnect_timer:
            pass
    

    # TODO


async def setup(bot) -> None:
    await bot.add_cog(MusicStream(bot))