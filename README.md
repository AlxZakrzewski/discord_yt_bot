# Selfhosted discord bot for playing music from Youtube.

## Commands
-`.p` - play audio from youtube video, example:
-`.p https://www.youtube.com/watch?v=dQw4w9WgXcQ`
-`.s` - stop all the songs and clear the queue
-`.skip` - skip current song

NOTE - bot has to download the audio first so there is a delay after play command is executed, in the past is was possible to play it directly from Youtube but this was blocked

## Prerequisites
1. Install [docker](https://docs.docker.com/engine/install/) on the Linux machine you will run bot
2. Setup empty discord bot with following [guide](https://discordpy.readthedocs.io/en/stable/discord.html), save token for the bot in save place and invite the bot to your server
3. Get cookies file from incognito tab from youtube main page when you are logged in, I did it with [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?hl=en)

## Running the bot
1. Login to the machine
2. Prepare cookies.txt file on the server
3. Run following docker run command:
```
docker run --rm -d --name bot_yt -v /path/to/your/cookies.txt:/app/cookies.txt -e TOKEN=<your bot token> babro/bot_yt
```

Bot should connect to your server, if your cookies.txt file is valid it should also play music from Youtube.
