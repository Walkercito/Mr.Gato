import os
import pathlib
import discord
from dotenv import load_dotenv


TOKEN = os.getenv("BOT_TOKEN")
BASE_DIR = pathlib.Path(__file__).parent

COG_DIR = BASE_DIR / "cogs"