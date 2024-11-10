import discord
from settings import TOKEN
from pathlib import Path
from discord.ext import commands
from rich import print
from rich.console import Console
from rich.traceback import install

install()  # Habilita el rastreo de errores mejorado con rich
console = Console()

def main():
    bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())


    @bot.event
    async def on_ready():
        console.print(f"[bold green]Initialized as {bot.user}[/bold green]")
        await bot.change_presence(activity=discord.Game(name="/help"))

        for file in Path('cogs').glob('**/*.py'):
            *tree, _ = file.parts
            extension_name = f"{'.'.join(tree)}.{file.stem}"
            if extension_name not in bot.extensions:
                try:
                    await bot.load_extension(extension_name)
                    console.print(f"[bold cyan]Loaded extension[/bold cyan]: {extension_name}")
                
                except Exception as e:
                    console.print(f"[bold red]Failed to load extension {extension_name}[/bold red]: {e}")

        await bot.tree.sync()
        console.print("[bold yellow]Command tree synchronized.[/bold yellow]")


    @bot.tree.command(name="ping", description="You say ping, I say Pong!")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(f"Pong in {latency} ms!")
        console.print(f"[bold magenta]Ping command used, latency:[/bold magenta] {latency} ms")


    bot.run(TOKEN)

if __name__ == "__main__":
    main()