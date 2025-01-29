import os
import pathlib
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
BASE_DIR = pathlib.Path(__file__).parent

COG_DIR = BASE_DIR / "cogs"

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'referer': 'https://www.youtube.com/',
    'cookiefile': 'cookies.txt',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}