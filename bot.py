#!/usr/bin/env python3
import os
import discord
from discord.ext import commands
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

# Create an instance of a bot with the new command prefix '.'
bot = commands.Bot(command_prefix=".", intents=intents)

# Set up the download directory
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')

@bot.command()
async def p(ctx, url: str):
    """Add a song to the queue and play it if not already playing"""
    global queue, is_playing

    # Add the song to the queue
    queue.append(url)
    print(queue)
    await ctx.send(f"Added to queue: {url}")

    # Start playback if not already playing
    if not is_playing:
        await play_next(ctx)

@bot.command()
async def s(ctx):
    """Stop playback and clear the queue"""
    global voice_client, queue, is_playing, downloaded_files

    if voice_client and voice_client.is_playing():
        voice_client.stop()  # Stop playing audio
        await ctx.send("Playback stopped.")
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
    await ctx.send("All downloaded files have been deleted.")

@bot.command()
async def skip(ctx):
    """Skip the current song and move to the next"""
    global voice_client

    if voice_client and voice_client.is_playing():
        voice_client.stop()  # Stop the current song
        await ctx.send("Skipped the current song.")
        await play_next(ctx)  # Immediately move to the next song in the queue
    else:
        await ctx.send("There is no song playing to skip.")

async def play_next(ctx):
    """Play the next song in the queue."""
    global queue, is_playing, voice_client, downloaded_files

    is_playing = False

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
    def after_playing(e):
        if mp3_file in downloaded_files:
            downloaded_files.remove(mp3_file)
            if os.path.exists(mp3_file):
                os.remove(mp3_file)

    try:
        voice_client.play(discord.FFmpegPCMAudio(mp3_file), after=after_playing)
        await ctx.send(f"Now playing: {url}")

    except Exception as e:
        logging.error(f"Error during playback: {e}")
        is_playing = False
        await play_next(ctx)

async def download_mp3(url: str):
    """Download the MP3 from the provided YouTube URL using yt-dlp CLI"""
    try:
        # Generate a unique file name for the MP3 based on the URL
        file_hash = hashlib.md5(url.encode()).hexdigest()
        mp3_file = os.path.join(DOWNLOAD_DIR, f'{file_hash}.mp3')

        # Run yt-dlp via subprocess to download the audio as MP3
        command = [
            'yt-dlp',
            '--format', 'bestaudio',  # Download the best audio format
            '--extract-audio',  # Extract audio only (no video)
            '--audio-format', 'mp3',
            '--output', mp3_file,  # Output file path
            '--cookies', 'cookies.txt',  # Use cookies file
            '--quiet',  # Suppress non-essential output
            url
        ]

        # Execute the command
        subprocess.run(command, check=True)

        return mp3_file
    except subprocess.CalledProcessError as e:
        logging.error(f"Error downloading audio: {e}")
        return None

# Run the bot with the token
bot.run(token)
