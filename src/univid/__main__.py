import os
import sys

import discord
from dotenv import load_dotenv

from .bot import Config, UnividBot


def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        sys.exit("DISCORD_TOKEN is not set (see .env.example)")

    config = Config(
        token=token,
        cookies_file=os.getenv("COOKIES_FILE") or None,
        max_duration=int(os.getenv("MAX_DURATION", "600")),
        max_concurrent=int(os.getenv("MAX_CONCURRENT", "2")),
    )
    discord.utils.setup_logging()
    UnividBot(config).run(config.token, log_handler=None)


if __name__ == "__main__":
    main()
