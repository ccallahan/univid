"""Discord client: watch for supported links and reply with the video."""

import asyncio
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

import discord

from .compress import TooLarge, fit_to_size
from .downloader import TooLong, download
from .links import extract_links

log = logging.getLogger(__name__)

WORKING = "⏳"
FAILED = "❌"
# Headroom under the guild limit for multipart overhead.
UPLOAD_MARGIN = 256 * 1024
# Small grey text under each video. <> keeps Discord from previewing the link.
FOOTER = "-# [Share or support univid](<https://linktr.ee/univid_bot>)"


@dataclass
class Config:
    token: str
    cookies_file: str | None = None
    max_duration: int = 600
    max_concurrent: int = 2


class UnividBot(discord.Client):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.config = config
        self.slots = asyncio.Semaphore(config.max_concurrent)

    async def on_ready(self):
        log.info("logged in as %s (%s)", self.user, self.user.id)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        links = extract_links(message.content)
        if not links:
            return

        await self._react(message.add_reaction, WORKING)
        posted = False
        failed = False
        for url in links:
            try:
                posted |= await self._handle(message, url)
            except Exception:
                log.exception("failed on %s", url)
                failed = True

        if posted:
            try:
                await message.edit(suppress=True)
            except discord.Forbidden:
                log.warning("no Manage Messages in #%s; can't hide embed", message.channel)
        await self._react(message.remove_reaction, WORKING, self.user)
        if failed:
            await self._react(message.add_reaction, FAILED)

    async def _handle(self, message: discord.Message, url: str) -> bool:
        """Download and post one video. Returns True if something was posted."""
        limit = message.guild.filesize_limit if message.guild else discord.utils.DEFAULT_FILE_SIZE_LIMIT_BYTES
        max_bytes = limit - UPLOAD_MARGIN

        async with self.slots:
            with tempfile.TemporaryDirectory(prefix="univid-") as tmp:
                try:
                    path = await download(
                        url, Path(tmp), max_bytes,
                        max_duration=self.config.max_duration,
                        cookies_file=self.config.cookies_file,
                    )
                    if path is None:
                        return False
                    path = await fit_to_size(path, max_bytes)
                except (TooLong, TooLarge) as e:
                    log.info("skipping %s: %s", url, e)
                    await message.reply("That video is too long to post here.", mention_author=False)
                    return False

                await message.reply(
                    FOOTER,
                    file=discord.File(path, filename=f"video{path.suffix}"),
                    mention_author=False,
                )
                log.info("posted %s (%d bytes)", url, path.stat().st_size)
                return True

    @staticmethod
    async def _react(fn, *args):
        try:
            await fn(*args)
        except discord.HTTPException:
            pass
