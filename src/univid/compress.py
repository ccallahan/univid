"""Re-encode a video with ffmpeg so it fits under Discord's upload limit."""

import asyncio
import os
from pathlib import Path

MIN_VIDEO_KBPS = 150
# Leave room for container overhead and bitrate overshoot.
SIZE_SAFETY = 0.92


class TooLarge(Exception):
    """The video can't be squeezed under the limit at watchable quality."""


def plan_encode(duration: float, max_bytes: int) -> tuple[int, int, int | None]:
    """Return (video_kbps, audio_kbps, max_height or None) for a target size."""
    if duration <= 0:
        raise ValueError("duration must be positive")
    total_kbps = max_bytes * 8 * SIZE_SAFETY / duration / 1000
    audio_kbps = 128 if total_kbps >= 1000 else 64
    video_kbps = int(total_kbps - audio_kbps)
    if video_kbps < MIN_VIDEO_KBPS:
        raise TooLarge(f"needs {video_kbps} kbps video for {duration:.0f}s")
    if video_kbps < 1000:
        height = 480
    elif video_kbps < 2500:
        height = 720
    else:
        height = None
    return video_kbps, audio_kbps, height


async def _run(*args: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        tail = err.decode(errors="replace").strip().splitlines()[-5:]
        raise RuntimeError(f"{args[0]} failed: " + " | ".join(tail))
    return out.decode()


async def probe_duration(path: Path) -> float:
    out = await _run(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    )
    return float(out.strip())


async def fit_to_size(src: Path, max_bytes: int) -> Path:
    """Return `src` if it already fits, otherwise a two-pass re-encode that does."""
    if src.stat().st_size <= max_bytes:
        return src

    duration = await probe_duration(src)
    video_kbps, audio_kbps, height = plan_encode(duration, max_bytes)
    dst = src.with_name(src.stem + ".small.mp4")
    passlog = str(src.with_name("ffpass"))

    common = ["ffmpeg", "-y", "-hide_banner", "-i", str(src)]
    if height:
        common += ["-vf", f"scale=-2:'min({height},ih)'"]
    common += [
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{video_kbps}k",
        "-pix_fmt", "yuv420p", "-passlogfile", passlog,
    ]

    await _run(*common, "-pass", "1", "-an", "-f", "null", os.devnull)
    await _run(
        *common, "-pass", "2", "-c:a", "aac", "-b:a", f"{audio_kbps}k",
        "-movflags", "+faststart", str(dst),
    )

    if dst.stat().st_size > max_bytes:
        raise TooLarge(f"re-encode came out at {dst.stat().st_size} bytes")
    return dst
