FROM frolvlad/alpine-python3

# Install ffmpeg
RUN apk add ffmpeg

# Install yt-dlp
RUN wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O /usr/bin/yt-dlp && \
    chmod a+rx /usr/bin/yt-dlp

WORKDIR /app

# Add bot user
RUN addgroup -S bot && adduser -S bot -G bot

COPY bot.py requirements.txt ./
RUN chown -R bot:bot /app
USER bot

RUN pip install --no-cache-dir -r requirements.txt

CMD ["./bot.py"]
