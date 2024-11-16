import discord
from discord.ext import commands
from pathlib import Path
from rich import print
from rich.console import Console
from rich.traceback import install
import threading
from flask import Flask
import os

# Configuración de Rich para rastreo mejorado
install()
console = Console()

# Inicializar Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "¡El servidor Flask está funcionando junto al bot de Discord!"

# Función principal
def main():
    TOKEN = os.environ["BOT_TOKEN"]

    # Inicializar el bot de Discord
    bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

    @bot.event
    async def on_ready():
        console.print(f"[bold green]Initialized as {bot.user}[/bold green]")
        await bot.change_presence(activity=discord.Game(name="with a mouse"))

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

    # Hilos para ejecutar Flask y el bot de Discord simultáneamente
    def run_flask():
        app.run(host="0.0.0.0", port=5000)

    def run_bot():
        bot.run(TOKEN)

    flask_thread = threading.Thread(target=run_flask)
    discord_thread = threading.Thread(target=run_bot)

    flask_thread.start()
    discord_thread.start()

    flask_thread.join()
    discord_thread.join()

if __name__ == "__main__":
    main()