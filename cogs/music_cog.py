import discord
import asyncio
from rich import print
from discord.ext import commands
from discord import app_commands
from rich.console import Console


console = Console()


class MusicStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.disconnect_timer = None

    
    async def cog_unload(self):
        if self.disconnect_timer:
            pass



    @commands.hybrid_command(name='join', description='Joins to the current VC you\'re in.')
    async def join_vc(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)

        if not ctx.author.voice:
            await ctx.send("*You must be inside of a VC to use this.*", ephemeral=True)
            return
        
        channel = ctx.author.voice.channel

        if self.voice_client:
            if self.voice_client.channel == channel:
                await ctx.send(f'I\'m already in the VC, use **/play** or **{self.bot.command_prefix}play** followed by the link or the name of a song to start playing!', ephemeral=True)
                return
            else:
                await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()
        
        await ctx.send(f'🔊 Connected to **{channel.name}**, use **/play** or **{self.bot.command_prefix}play** followed by the link or the name of a song to start playing!', ephemeral=True)
    
    
    
    @commands.hybrid_command(name = 'leave', description = 'Takes out the bot of the current VC.')
    async def leave_vc(self, ctx: commands.Context):
        if self.voice_client:
            channel = ctx.author.voice.channel
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send(f'🔇 Disconnected from **{channel.name}**')
        
        else:
            await ctx.send('🤖 **I\'m not in a VC**')


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        if self.voice_client:
            bot_channel = self.voice_client.channel

            if before.channel == bot_channel and len(bot_channel.members) == 1:
                if self.disconnect_timer:
                    self.disconnect_timer.cancel()

                self.disconnect_timer = asyncio.create_task(self.start_disconnect_timer())
            
            elif after.channel == bot_channel and self.disconnect_timer:
                self.disconnect_timer.cancel()
                self.disconnect_timer = None


    
    async def start_disconnect_timer(self):
        await asyncio.sleep(30)

        if self.voice_client and len(self.voice_client.channel.members) == 1:
            await self.voice_client.disconnect()
            self.voice_client = None



async def setup(bot) -> None:
    await bot.add_cog(MusicStream(bot))