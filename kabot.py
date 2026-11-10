#!/usr/bin/env python3

"""Kabot"""

import asyncio
import logging
import sys
from glob import glob
from os import environ
from os.path import isfile
from random import randint, random
from signal import SIGINT, SIGTERM

import discord
from yaml import safe_load

logger = logging.getLogger(__name__)


class Kabot(discord.Client):
    """Kabot"""

    def __init__(self, conf):
        intents = discord.Intents.default()
        intents.typing = False
        intents.presences = False
        super().__init__(intents=intents)
        self._conf = conf
        self._files = []
        audio_expr = conf.get("files")
        if isinstance(audio_expr, str):
            audio_expr = [audio_expr]
        for expr in audio_expr:
            audio_files = glob(expr, recursive=True)
            for audio_file in audio_files:
                if isfile(audio_file):
                    self._files.append(audio_file)
                else:
                    logger.error("%s is not a file", audio_file)
        self._tasks = []

    def _create_tasks(self):
        """Create guild tasks"""
        for guild in self.guilds:
            interval = self._conf["default"]["interval"]
            for conf in self._conf["servers"]:
                if conf["name"] == guild.name:
                    interval = conf.get("interval") or interval
                    break
            task = asyncio.create_task(self.guild_timer(guild, interval))
            self._tasks.append(task)

    async def on_ready(self):
        """On ready"""
        logger.info("Logged in as %s", self.user)
        logger.info("Guilds: %s", ", ".join([guild.name for guild in self.guilds]))
        self._create_tasks()

    async def play_random_clip(self, voice_chan):
        """Play a random audio clip on the specified voice channel"""
        logger.info(
            "Playing audio clip on %s for %d members",
            voice_chan.name,
            len(voice_chan.members),
        )
        audio_file = self._files[randint(0, len(self._files) - 1)]
        try:
            audio_source = discord.FFmpegPCMAudio(audio_file)
        except Exception as err:
            logger.error(err)
            return
        try:
            voice_client = await voice_chan.connect()
        except Exception as err:
            logger.error(err)
            return
        try:
            voice_client.play(audio_source)
            while voice_client.is_playing():
                await asyncio.sleep(1)
        except Exception as err:
            logger.error(err)
        await voice_client.disconnect()

    async def guild_task(self, guild):
        """Check for users in guild voice channels"""
        annoyance = self._conf["default"]["annoyance"]
        for conf in self._conf["servers"]:
            if conf["name"] == guild.name:
                annoyance = conf.get("annoyance") or annoyance
                break
        for voice_chan in guild.voice_channels:
            if len(voice_chan.members) > 0 and random() <= annoyance:
                await self.play_random_clip(voice_chan)

    async def guild_timer(self, guild, interval):
        """Launch guild task at each interval"""
        while True:
            i = interval
            while i > 0:
                i -= 1
                await asyncio.sleep(1)
            await self.guild_task(guild)

    async def close(self):
        """Close"""
        for task in self._tasks:
            task.cancel()
        await super().close()
        logger.info("Logged out")


def configure_logging():
    """Configure logging, omitting the timestamp when journald already adds one"""
    if "JOURNAL_STREAM" in environ:
        logging.basicConfig(format="[%(name)s] %(message)s", level=logging.INFO)
    else:
        logging.basicConfig(
            format="%(asctime)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.INFO,
        )


async def kabot(conf):
    """Main function"""
    configure_logging()
    kabot = Kabot(conf)
    loop = asyncio.get_event_loop()
    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(kabot.close()))
    await kabot.start(conf["token"])
    logger.info("Exiting")


def main():
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <CONF>")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as conf_file:
            cfg = safe_load(conf_file)
    except (FileNotFoundError, PermissionError) as err:
        print(f"Failed to parse configuration: {err}")
        sys.exit(1)

    asyncio.run(kabot(cfg))


if __name__ == "__main__":
    main()
