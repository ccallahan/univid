"""Download a video with yt-dlp."""

import asyncio
import logging
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError

log = logging.getLogger(__name__)

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov"}


class TooLong(Exception):
    """The video is longer than the configured maximum duration."""


def _download_sync(
    url: str, workdir: Path, max_bytes: int, max_duration: int, cookies_file: str | None
) -> Path | None:
    too_long: list[str] = []

    def match_filter(info, *, incomplete):
        duration = info.get("duration")
        if duration and duration > max_duration:
            too_long.append(f"{duration:.0f}s > {max_duration}s")
            return "video too long"
        return None

    opts = {
        # Prefer formats already under the limit, else take the best and re-encode later.
        "format": f"bv*[filesize<?{max_bytes}]+ba/b[filesize<?{max_bytes}]/bv*+ba/b",
        # H.264/AAC plays inline in every Discord client; cap at 1080p to keep files small.
        "format_sort": ["res:1080", "vcodec:h264", "acodec:aac"],
        "merge_output_format": "mp4",
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "playlist_items": "1",  # posts with several videos: just the first
        "match_filter": match_filter,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    if cookies_file:
        opts["cookiefile"] = cookies_file

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
    except DownloadError as e:
        # Text-only tweets, photo-only posts, etc. aren't failures, just nothing to do.
        if "no video" in str(e).lower():
            log.info("no video at %s", url)
            return None
        raise

    if too_long:
        raise TooLong(too_long[0])

    files = [p for p in workdir.iterdir() if p.suffix in VIDEO_EXTS]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_size)


async def download(
    url: str,
    workdir: Path,
    max_bytes: int,
    max_duration: int = 600,
    cookies_file: str | None = None,
) -> Path | None:
    """Download `url` into `workdir`. Returns the video path, or None if there's no video."""
    return await asyncio.to_thread(
        _download_sync, url, workdir, max_bytes, max_duration, cookies_file
    )


if __name__ == "__main__":
    # Smoke test without Discord: python -m univid.downloader <url> [max_mb]
    import os
    import sys
    import tempfile

    from .compress import fit_to_size

    logging.basicConfig(level=logging.INFO)
    target = sys.argv[1]
    limit = int(float(sys.argv[2] if len(sys.argv) > 2 else 10) * 1024 * 1024)

    async def main():
        out = Path(tempfile.mkdtemp(prefix="univid-"))
        path = await download(target, out, limit, cookies_file=os.getenv("COOKIES_FILE"))
        if path is None:
            print("no video found")
            return
        print(f"downloaded {path} ({path.stat().st_size / 1e6:.1f} MB)")
        final = await fit_to_size(path, limit)
        print(f"final      {final} ({final.stat().st_size / 1e6:.1f} MB)")

    asyncio.run(main())
