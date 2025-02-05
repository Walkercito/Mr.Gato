import re
import discord
import asyncio
import yt_dlp
from rich import print
from discord.ext import commands
from discord import app_commands
from rich.console import Console

from settings import YTDL_OPTIONS, ffmpeg_options


console = Console()
def search_youtube(query: str) -> dict:
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
        try:
            if re.match(r'^(https?:\\/\\/)?(www\\.)?(youtube\\.com|youtu\\.?be)\\/.+', query, re.IGNORECASE):
                info = ytdl.extract_info(query, download = False)
                return {
                    'title': info['title'], 
                    'url': info['url'], 
                    'duration': info['duration'], 
                    'thumbnail': info.get('thumbnail', 'https://via.placeholder.com/150')  # Default placeholder image
                }
            else:
                info = ytdl.extract_info(f'ytsearch:{query}', download = False)
                if info:
                    entry = info['entries'][0]
                    return {
                        'title': entry['title'], 
                        'url': entry['url'], 
                        'duration': entry['duration'], 
                        'thumbnail': entry.get('thumbnail', 'https://via.placeholder.com/150')  # Default placeholder image
                    }
                return None
        
        except yt_dlp.utils.DownloadError as e:
            print(f"[bold red]YouTube Download Error:[/bold red] {e}")
        
        except Exception as e:
            print(f"[bold red]Fatal error:[/bold red] {e}")
        return None


def format_duration(seconds):
    minutes, secs = divmod(seconds, 60)
    return f'{minutes:02d}:{secs:02d}'


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
            self.disconnect_timer.cancel()
    
    
    @commands.hybrid_command(name = 'join', description = 'Joins to the current VC you\'re in.')
    async def join_vc(self, ctx: commands.Context):
        await ctx.defer(ephemeral = True)
        
        if not ctx.author.voice:
            embed = discord.Embed(
                title = '❌ Oops!',
                description = 'You must be inside of a VC to use this.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed, ephemeral = True)
            return
        
        channel = ctx.author.voice.channel
        if self.voice_client:
            if self.voice_client.channel == channel:
                embed = discord.Embed(
                    title = '🎧 I\'m here!',
                    description = f'I\'m already in the VC, use **/play** or **{self.bot.command_prefix}play** followed by the link or the name of a song to start playing!',
                    colour = discord.Colour.purple()
                )
                await ctx.send(embed = embed, ephemeral = True)
                return
            else:
                await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()

        await self.voice_client.guild.change_voice_state(channel = channel, self_mute = False, self_deaf = True)
        
        embed = discord.Embed(
            title = f'🔊 Connected to {channel.name}',
            description = f'Use **/play** or **{self.bot.command_prefix}play** followed by the link or the name of a song to start playing it.',
            colour = discord.Colour.dark_purple()
        )
        await ctx.send(embed = embed, ephemeral = False)
    
    
    @commands.hybrid_command(name = 'leave', description = 'Takes out the bot of the current VC.')
    async def leave_vc(self, ctx: commands.Context):
        await ctx.defer(ephemeral = True)

        if self.voice_client:
            channel_name = self.voice_client.channel.name

            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
            
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing = False
            self.is_paused = False
            self.queue.clear()
            
            embed = discord.Embed(
                title = '🔇 Disconnected',
                description = f'from **{channel_name}**.',
                colour = discord.Colour.purple()
            )
            await ctx.send(embed = embed, ephemeral = False)
        else:
            embed = discord.Embed(
                title = '🤖 Not in VC',
                description = 'I\'m not in a VC.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed, ephemeral = True)
    
    
    @commands.hybrid_command(name = 'play', description='Starts playing a song or adds one to the queue.')
    @app_commands.describe(song = 'The name or the link of the song you want to listen')
    async def play_track(self, ctx: commands.Context, song: str = None):
        await ctx.defer(ephemeral = True)
        
        if not song:
            embed = discord.Embed(
                title = '❌ Missing Argument',
                description = 'Please provide a song name or URL.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed, ephemeral = True)
            return

        if not ctx.author.voice:
            embed = discord.Embed(
                title = '❌ Oops!',
                description = 'You must be inside of a VC to use this.',
                colour=discord.Colour.red()
            )
            await ctx.send(embed = embed, ephemeral = True)
            return

        if not self.voice_client:
            channel = ctx.author.voice.channel
            self.voice_client = await channel.connect()
            await self.voice_client.guild.change_voice_state(channel = channel, self_mute = False, self_deaf = True)
            embed = discord.Embed(
                title = f'🔊 Connected to {channel.name}',
                description = f'Bot joined the voice channel and will now play your song.',
                colour = discord.Colour.dark_purple()
            )
            await ctx.send(embed = embed, ephemeral = False)

        track = search_youtube(song)
        if not track:
            embed = discord.Embed(
                title = '❌ No Results',
                description = 'Couldn\'t find any results right now.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed, ephemeral = True)
            return

        self.queue.append({
            'title': track['title'],
            'url': track['url'],
            'duration': track['duration'],
            'thumbnail': track['thumbnail']
        })
        formatted_duration = format_duration(track['duration'])
        embed = discord.Embed(
            title = '✅ Added to Queue',
            description = f'**{track["title"]}**\nDuration: {formatted_duration}',
            colour = discord.Colour.pink()
        )
        await ctx.send(embed = embed)

        if not self.is_playing:
            await self.play_next(ctx)
    
    
    @commands.hybrid_command(name = 'pause', description = 'Pauses the current song.')
    async def pause_track(self, ctx: commands.Context):
        if self.voice_client and self.is_playing:
            self.voice_client.pause()
            self.is_paused = True

            formatted_duration = format_duration(self.current_track['duration'])
            embed = discord.Embed(
                title = '⏸️ Paused',
                description = f'{self.current_track["title"]}\nDuration: {formatted_duration}',
                colour = discord.Colour.orange()
            )
            await ctx.send(embed = embed)
    
    
    @commands.hybrid_command(name = 'resume', description = 'Continue playing the current song.')
    async def resume_track(self, ctx: commands.Context):
        if self.voice_client and self.is_paused:
            self.voice_client.resume()
            self.is_paused = False
            self.is_playing = True

            formatted_duration = format_duration(self.current_track['duration'])
            embed = discord.Embed(
                title = '🎶 Continue playing',
                description = f'**{self.current_track["title"]}**\nDuration: {formatted_duration}',
                colour = discord.Colour.purple()
            )
            thumbnail_url = self.current_track.get('thumbnail', 'https://via.placeholder.com/150')
            embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text = f'Requested by {ctx.author.name}')
            await ctx.send(embed = embed)
    
    
    @commands.hybrid_command(name = 'skip', description = 'Jumps to the next song in the queue.')
    async def skip_track(self, ctx: commands.Context):
        if self.voice_client and (self.is_paused or self.is_playing):
            self.voice_client.stop()
            
            formatted_duration = format_duration(self.current_track['duration'])
            embed = discord.Embed(
                title = '⏭️ Skipped',
                description = f'{self.current_track["title"]}\nDuration: {formatted_duration}',
                colour = discord.Colour.orange()
            )
            await ctx.send(embed = embed)
    
    
    @commands.hybrid_command(name = 'queue', description = 'Shows the current music queue.')
    async def show_queue(self, ctx: commands.Context):
        if not self.queue:
            embed = discord.Embed(
                title = '🎶 Queue',
                description = 'The queue is currently empty.',
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            return

        queue_list = []
        for index, track in enumerate(self.queue, 1):
            formatted_duration = format_duration(track['duration'])
            queue_list.append(f'{index}. **{track["title"]}** - Duration: {formatted_duration}')

        queue_str = '\n'.join(queue_list)
        embed = discord.Embed(
            title = '🎶 Queue',
            description = queue_str if queue_str else 'No songs in queue.',
            colour = discord.Colour.blue()
        )
        embed.set_footer(text = f'Number of tracks: {len(self.queue)}')
        await ctx.send(embed = embed)
    
    
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
        if self.queue:
            self.current_track = self.queue.pop(0)
            source = discord.FFmpegPCMAudio(self.current_track['url'], **ffmpeg_options)
            self.voice_client.play(source, after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            self.is_playing = True
            
            formatted_duration = format_duration(self.current_track['duration'])
            embed = discord.Embed(
                title = '🎶 Now Playing',
                description = f'[{self.current_track['title']}]({self.current_track['url']})',
                colour = discord.Colour.purple()
            )
            embed.add_field(name = 'Duration', value = f'`{formatted_duration}`')
            embed.add_field(name = 'Queue', value = f'{len(self.queue)}')
            thumbnail_url = self.current_track.get('thumbnail', 'https://via.placeholder.com/150')
            embed.set_thumbnail(url = thumbnail_url)
            embed.set_footer(text = f'Requested by {ctx.author.name}')
            await ctx.send(embed = embed)
        
        else:
            self.is_playing = False
            embed = discord.Embed(
                title = '🎶 Queue Ended',
                description = 'No more songs in the queue.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)


async def setup(bot) -> None:
    await bot.add_cog(MusicStream(bot))