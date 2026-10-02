FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY README.md ./
COPY src ./src
# Sites change constantly and yt-dlp keeps up, so always take the newest release
# at build time rather than whatever uv.lock pinned.
RUN uv sync --frozen --no-dev && uv pip install --upgrade "yt-dlp[default]"

RUN useradd --create-home univid
USER univid
# Run the venv directly; `uv run` would re-sync and undo the yt-dlp upgrade.
CMD [".venv/bin/python", "-m", "univid"]
