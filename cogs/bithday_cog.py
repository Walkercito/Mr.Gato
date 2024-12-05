import discord
import typing
import sqlite3
import asyncio
from datetime import datetime
from discord.ext import commands, tasks
from discord import app_commands


class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_database()
        self.check_birthdays.start()

    
    def create_database(self):
        try:
            conn = sqlite3.connect('data/birthdays.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS birthdays (
                    user_id INTEGER PRIMARY KEY,
                    day INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    year INTEGER NOT NULL
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    
    def get_month_number(self, month_name):
        months = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        return months.get(month_name)

    
    async def send_birthday_message(self, guild: discord.Guild, member: discord.Member, birth_year: int):
        general_channel = discord.utils.get(guild.text_channels, name='general')
        if not general_channel:
            general_channel = guild.system_channel
        
        
        if general_channel:
            age = datetime.now().year - birth_year
            embed = discord.Embed(
                title="🎂 Happy Birthday! 🎉",
                description=f"Happy {age}th Birthday, {member.mention}! 🎈\nHave an amazing day! 🎊🎁",
                color=discord.Color.gold()
            )
            await general_channel.send(content=f"@everyone", embed=embed)

    @app_commands.command(name="birthday", description="Set your birthday")
    async def birthday(self, interaction: discord.Interaction, 
                      day: int, 
                      month: typing.Literal["January", "February", "March", "April", "May", "June", 
                                          "July", "August", "September", "October", "November", "December"], 
                      year: int):
        try:
            conn = sqlite3.connect('data/birthdays.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT day, month, year FROM birthdays WHERE user_id = ?', (interaction.user.id,))
            existing_birthday = cursor.fetchone()
            
            if existing_birthday:
                day, month, year = existing_birthday
                embed = discord.Embed(
                    title="Birthday Already Set! 🎂",
                    description=f"Your birthday is already set to: {month} {day}, {year}\nUse /updatebirthday if you need to change it.",
                    colour=discord.Colour.yellow(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                conn.close()
                return

            month_days = {
                1: 31, 2: 29 if year % 4 == 0 else 28, 3: 31, 4: 30,
                5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
            }
            
            month_num = self.get_month_number(month)
            
            if not (1 <= day <= month_days[month_num]):
                await interaction.response.send_message(
                    f"Invalid day for {month}! This month has {month_days[month_num]} days.",
                    ephemeral=True
                )
                return

            current_year = datetime.now().year
            if not (1900 <= year <= current_year):
                await interaction.response.send_message(
                    "Please enter a valid year between 1900 and the current year.",
                    ephemeral=True
                )
                return

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS birthdays (
                    user_id INTEGER PRIMARY KEY,
                    day INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    year INTEGER NOT NULL
                )
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO birthdays (user_id, day, month, year)
                VALUES (?, ?, ?, ?)
            ''', (interaction.user.id, day, month, year))
            
            conn.commit()
            conn.close()

            embed = discord.Embed(
                title="Birthday set! 🎂",
                description=f"Your birthday has been set to: {month} {day}, {year}\nWe'll let everyone know when your birthday is! 🎉",
                colour=discord.Colour.blurple(),
            )
            
            await interaction.response.send_message(embed=embed)

            now = datetime.now()
            if now.day == day and now.strftime("%B") == month:
                await asyncio.sleep(1)
                await self.send_birthday_message(interaction.guild, interaction.user, year)
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            await interaction.response.send_message(
                "There was an error saving your birthday. Please try again later.",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True
            )

    
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        try:
            await self.bot.wait_until_ready()
            
            now = datetime.now()
            current_month_name = now.strftime("%B")
            current_day = now.day

            conn = sqlite3.connect('data/birthdays.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, year FROM birthdays 
                WHERE month = ? AND day = ?
            ''', (current_month_name, current_day))
            
            birthday_users = cursor.fetchall()
            conn.close()

            for user_id, birth_year in birthday_users:
                for guild in self.bot.guilds:
                    member = guild.get_member(user_id)
                    if member:
                        await self.send_birthday_message(guild, member, birth_year)
                            
        except Exception as e:
            print(f"Error in check_birthdays: {e}")

    
    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = datetime.combine(now.date(), datetime.min.time())
        if now.hour >= 0:
            next_run = next_run.replace(day=now.day + 1)
        await discord.utils.sleep_until(next_run)

    
    def cog_unload(self):
        self.check_birthdays.cancel()


async def setup(bot):
    await bot.add_cog(Birthday(bot))