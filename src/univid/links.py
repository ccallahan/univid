"""Find supported video links in a Discord message."""

import re
from urllib.parse import urlparse

# Optional leading "<" so we can detect (and skip) links the user deliberately
# wrapped to suppress Discord's embed. "|" is excluded so ||spoiler|| links parse.
_URL_RE = re.compile(r"(<)?(https?://[^\s<>|]+)(>)?")
_TRAILING_PUNCT = ".,;:!?)]}'\""

# Hosts we try to download from. Subdomains (www., m., mobile., vm., ...) match too.
# YouTube is deliberately absent: Discord already embeds it fine.
SUPPORTED_DOMAINS = (
    "facebook.com",
    "fb.watch",
    "instagram.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
    "reddit.com",
    "redd.it",
    "threads.net",
    "threads.com",
    "bsky.app",
)


def is_supported(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in SUPPORTED_DOMAINS)


def extract_links(content: str, limit: int = 3) -> list[str]:
    """Return up to `limit` unique supported URLs, in the order they appear."""
    found: list[str] = []
    for m in _URL_RE.finditer(content):
        if m.group(1) and m.group(3):
            continue  # <url> means the user doesn't want an embed
        url = m.group(2).rstrip(_TRAILING_PUNCT)
        if is_supported(url) and url not in found:
            found.append(url)
            if len(found) >= limit:
                break
    return found
