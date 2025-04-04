#!/usr/bin/env python3
import os
import discord
from discord.ext import commands, tasks
from pytube import Playlist
import subprocess
import asyncio
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Retrieve token from environment variable
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN environment variable is not set!")

intents = discord.Intents.default()
intents.message_content = True

# Global variables
voice_client = None
queue = []  # Queue to store song URLs
is_playing = False  # Flag to indicate if a song is currently being played
downloaded_files = []  # List to store paths of downloaded MP3 files
inactive_seconds = 0  # Counter for inactivity in seconds

# Create an instance of a bot with the new command prefix '.'
bot = commands.Bot(command_prefix=".", intents=intents)

# Set up the download directory
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    inactivity_checker.start()

@bot.command()
async def join(ctx):
    """Join the voice channel of the user who issued the command."""
    global voice_client
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if not voice_client or not voice_client.is_connected():
            voice_client = await channel.connect()
    else:
        await ctx.send("You must be in a voice channel for me to join!")

@bot.command()
async def leave(ctx):
    """Leave the current voice channel."""
    global voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        voice_client = None

@bot.command()
async def p(ctx, url: str):
    """Add a song to the queue and play it."""
    global queue, is_playing

    # Ensure the bot is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You must be in a voice channel for me to play music!")
        return
    if not voice_client or not voice_client.is_connected():
        await join(ctx)

    # Add the song to the queue
    queue.append(url)

    # Start playback if not already playing
    if not is_playing:
        await play_next(ctx)

@bot.command()
async def pl(ctx, url: str):
    global queue, is_playing

    # Ensure the bot is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You must be in a voice channel for me to play music!")
        return
    if not voice_client or not voice_client.is_connected():
        await join(ctx)

    playlist = Playlist(url)
    for url in playlist:
        queue.append(url)

    # Start playback if not already playing
    if not is_playing:
        await play_next(ctx)

@bot.command()
async def s(ctx):
    """Stop playback and clear the queue."""
    global voice_client, queue, is_playing, downloaded_files

    if voice_client and voice_client.is_playing():
        voice_client.stop()  # Stop playing audio
    else:
        await ctx.send("The bot is not playing anything.")

    # Clear the queue, reset playback state, and delete downloaded files
    queue.clear()
    is_playing = False

    # Remove all downloaded MP3 files
    for file in downloaded_files:
        if os.path.exists(file):
            os.remove(file)
    downloaded_files.clear()

@bot.command()
async def skip(ctx):
    """Skip the current song and move to the next."""
    global voice_client

    if voice_client and voice_client.is_playing():
        voice_client.stop()  # Stop the current song
        await play_next(ctx)  # Immediately move to the next song in the queue
    else:
        await ctx.send("There is no song playing to skip.")

async def play_next(ctx):
    """Play the next song in the queue."""
    global queue, is_playing, voice_client, downloaded_files

    if not queue:
        is_playing = False
        return

    is_playing = True

    # Get the next URL from the queue
    url = queue.pop(0)

    # Download the MP3 file
    mp3_file = await download_mp3(url)
    if not mp3_file:
        await ctx.send(f"Failed to download audio: {url}")
        is_playing = False
        await play_next(ctx)  # Skip to the next song
        return

    # Keep track of the downloaded file
    downloaded_files.append(mp3_file)

    # Play the MP3 file in the voice channel
    try:
        def after_playing(e):
            coro = play_next(ctx)
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                fut.result()
            except Exception as ex:
                logging.error(f"Error after playing audio: {ex}")

        voice_client.play(discord.FFmpegPCMAudio(mp3_file), after=after_playing)

    except Exception as e:
        logging.error(f"Error during playback: {e}")
        is_playing = False
        await play_next(ctx)

async def download_mp3(url: str):
    """Download the MP3 from the provided YouTube URL using yt-dlp CLI."""
    try:
        # Generate a unique file name for the MP3 based on the URL
        file_hash = hashlib.md5(url.encode()).hexdigest()
        mp3_file = os.path.join(DOWNLOAD_DIR, f'{file_hash}.mp3')

        # Ensure the cookies file exists
        cookies_file = 'cookies.txt'
        if not os.path.exists(cookies_file):
            logging.error("Cookies file 'cookies.txt' is missing!")
            return None

        # Run yt-dlp via subprocess to download the audio as MP3
        command = [
            'yt-dlp',
            '--format', 'bestaudio/best',  # Download the best audio format
            '--extract-audio',  # Extract audio only (no video)
            '--audio-format', 'mp3',
            '--output', mp3_file,  # Output file path
            '--cookies', cookies_file  # Use cookies file
        ]

        # Execute the command
        subprocess.run(command + [url], check=True)

        return mp3_file
    except subprocess.CalledProcessError as e:
        logging.error(f"Error downloading audio: {e}")
        return None

@tasks.loop(seconds=10)
async def inactivity_checker():
    """Check for inactivity and disconnect if inactive for 5 minutes."""
    global inactive_seconds, voice_client, is_playing

    if voice_client and not is_playing and not queue:
        inactive_seconds += 10
        if inactive_seconds >= 300:  # 5 minutes
            await voice_client.disconnect()
            voice_client = None
            inactive_seconds = 0
            logging.info("Disconnected due to inactivity.")
    else:
        inactive_seconds = 0  # Reset inactivity timer if playing or queue is not empty

# Run the bot with the token
bot.run(token)
