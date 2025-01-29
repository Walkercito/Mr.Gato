import discord
import asyncio
import ffmpeg
import yt_dlp
from rich import print
from discord.ext import commands
from rich.console import Console

from settings import YTDL_OPTIONS, ffmpeg_options


console = Console()
def search_youtube(query: str) -> dict:
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as  ytdl:
        try:
            info = ytdl.extract_info(f'ytsearch:{query}', download = False)
            return info['entries'][0] if info else None

        except Exception as e:
            console.print(f"[bold red]Fatal error:[/bold red] {e}")
            return None


class MusicStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.disconnect_timer = None

        self.queue = []
        self.current_track = None
        self.is_playing = False
        self.is_paused = False

    
    async def cog_unload(self):
        if self.disconnect_timer:
            pass


    @commands.hybrid_command(name='join', description='Joins to the current VC you\'re in.')
    async def join_vc(self, ctx: commands.Context):
        await ctx.defer(ephemeral = True)

        if not ctx.author.voice:
            await ctx.send("*You must be inside of a VC to use this.*", ephemeral = True)
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
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing = False
            self.is_paused = False
            self.queue.clear()
            await ctx.send(f'🔇 Disconnected from **{channel.name}**.')
        
        else:
            await ctx.send('🤖 **I\'m not in a VC.**')

    
    @commands.hybrid_command(name = 'play', description = 'Starts playing a song or adds one to the queue.')
    async def play_track(self, ctx: commands.Context, query: str):
        await ctx.defer(ephemeral = True)

        if not ctx.author.voice:
            await ctx.send("*You must be inside of a VC to use this.*", ephemeral = True)
            return

        track = search_youtube(query)
        if not track:
            await ctx.send('❌ Couldn\'t find any results right now.', ephemeral = True)
            return

        self.queue.append(
            {
                'title': track['title'],
                'url': track['url'],
                'duration': track['duration']
            }
        )
        await ctx.send(f'✅ Added to the queue **{track['title']}**.')
        if not self.is_playing:
            await self.play_next(ctx)

    
    @commands.hybrid_command(name = 'pause', description = 'Pauses the current song.')
    async def pause_track(self, ctx: commands.Context):
        if self.voice_client and self.is_playing:
            self.voice_client.pause()
            self.is_paused = True
            await ctx.send('⏸️ Song paused')

    @commands.hybrid_command(name = 'resume', description = 'Continue playing the current song.')
    async def resume_track(self, ctx: commands.Context):
        if self.voice_client and self.is_paused:
            self.voice_client.resume()
            self.is_paused = False
            self.is_playing = True
            await ctx.send(f'🎶 Continue playing: **{self.current_track['title']}**.')
    


    @commands.hybrid_command(name = 'skip', description = 'Jumps to the next song in the queue.')
    async def skip_tack(self, ctx: commands.Context):
        if self.voice_client and (self.is_paused or self.is_playing):
            self.voice_client.stop()
            await ctx.send('⏭️ Song skiped')


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

    
    async def start_disconnect_timer(self) -> None:
        await asyncio.sleep(30)

        if self.voice_client and len(self.voice_client.channel.members) == 1:
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
            
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing = False
            self.is_paused = False
    


    async def play_next(self, ctx: commands.Context):
        if len(self.queue) > 0:
            self.current_track = self.queue.pop(0)

            source = discord.FFmpegPCMAudio(self.current_track['url'], **ffmpeg_options)
            self.voice_client.play(source, after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            self.is_playing = True

            await ctx.send(f'🎶 Playing: **{self.current_track['title']}** ')
        
        else:
            self.is_playing = False




async def setup(bot) -> None:
    await bot.add_cog(MusicStream(bot))