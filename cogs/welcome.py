import io
import aiohttp
import discord
import numpy as np
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageOps

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    def create_gradient(self, width, height, color1, color2):
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        color1_rgb = hex_to_rgb(color1)
        color2_rgb = hex_to_rgb(color2)
        
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        
        for x in range(width):
            r = int(color1_rgb[0] + (color2_rgb[0] - color1_rgb[0]) * (x / width))
            g = int(color1_rgb[1] + (color2_rgb[1] - color1_rgb[1]) * (x / width))
            b = int(color1_rgb[2] + (color2_rgb[2] - color1_rgb[2]) * (x / width))
            arr[:, x] = [r, g, b]
            
        return Image.fromarray(arr)

    
    async def create_welcome_banner(self, avatar_url):
        gradient = self.create_gradient(800, 250, '#2E3192', '#1BFFFF')
        banner = gradient.convert('RGBA')
        draw = ImageDraw.Draw(banner)

        async with aiohttp.ClientSession() as session:
            async with session.get(str(avatar_url)) as resp:
                avatar_data = await resp.read()
                avatar = Image.open(io.BytesIO(avatar_data)).convert('RGBA')

        avatar = avatar.resize((150, 150))

        mask = Image.new('L', (150, 150), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 150, 150), fill=255)

        output = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
        output.paste(avatar, (0, 0))
        output.putalpha(mask)

        banner.paste(output, (325, 50), output)

        with io.BytesIO() as image_binary:
            banner.save(image_binary, 'PNG')
            image_binary.seek(0)
            return discord.File(fp=image_binary, filename='welcome.png')


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            welcome_banner = await self.create_welcome_banner(member.display_avatar.url)
            embed = discord.Embed(
                description = f" > Welcome {member.mention}!",
                color = discord.Color.from_rgb(46, 49, 146) 
            )
            embed.set_image(url="attachment://welcome.png")
            await member.guild.system_channel.send(file=welcome_banner, embed=embed)



async def setup(bot):
    await bot.add_cog(Welcome(bot))