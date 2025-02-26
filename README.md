# Kabot

A simple Discord bot that randomly plays random audio files on random voice
channels.

## Usage

### Prerequisites

Create a Discord bot and get its access token.

Invite your bot to your Discord server(s). The bot might require some
permissions related to voice (connect, speak).

The `discord.py[voice]` Python library requires `ffmpeg` to play audio files.
Install it with for instance:

```bash
apt install ffmpeg
```

### Configuration

Create a folder named for instance `audio` with your audio files.

Put your bot token and configuration in [kabot.yaml](kabot.yaml):

```yaml
token: YOUR_DISCORD_TOKEN
# Audio files to play (can be a glob or list of globs).
files: audio/*.mp3
# Default bot settings.
default:
  interval: 960  # Interval in seconds between channels checks.
  annoyance: 0.2  # Probability to play a file (0 never, 1 always).
# Optional server specific configuration
servers:
  - name: ExampleServer
    interval: 3600
    annoyance: 1
```

This example configuration will make the bot check voice channels every 16
minutes (960 seconds). If some user is connected to a channel, the bot will
have 20% chance to play a random audio file from the `audio` folder. On
`ExampleServer`, the bot will play a random file every hour (if users are on
voice).

### Run

Install the application and dependencies with pip:

```bash
pip install .
```

Run Kabot:

```bash
kabot kabot.yaml
```
