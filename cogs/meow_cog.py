import discord
from discord.ext import commands
from discord import app_commands
from discord import app_commands

class Meow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name = "meow", description="The bot says meow")
    async def meowing(self, interaction: discord.Interaction):
        await interaction.response.send_message("Meow!")


async def setup(bot):
    await bot.add_cog(Meow(bot))