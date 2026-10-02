# univid

A Discord bot that watches for links to Facebook, Instagram, X/Twitter, TikTok, Reddit, Threads and Bluesky. It downloads the video with [yt-dlp](https://github.com/yt-dlp/yt-dlp) and replies with the file attached, so anyone can watch it in Discord without an account.

- Videos over the server's upload limit (10 MB, or more on boosted servers) are re-encoded with ffmpeg to fit.
- The bot hides the original message's broken or login-walled embed. This needs the Manage Messages permission.
- Links wrapped in `<...>` are ignored, the same way Discord ignores them for embeds.
- Posts with no video (text-only tweets, photo posts) are silently skipped.

## Discord setup

1. Go to https://discord.com/developers/applications, click **New Application**, then open **Bot**.
2. Under **Privileged Gateway Intents**, enable **Message Content Intent**.
3. Click **Reset Token** and copy the token into `.env` as `DISCORD_TOKEN`.
4. Invite the bot. Under **OAuth2 → URL Generator**, select the scope `bot` and these permissions:
   View Channels, Send Messages, Attach Files, Read Message History, Add Reactions, Manage Messages.

## Run locally

```sh
cp .env.example .env   # fill in DISCORD_TOKEN
uv run python -m univid
```

Requires `ffmpeg` on your PATH.

## Run with Docker

```sh
cp .env.example .env
docker compose up -d --build
```

Sites change their internals often, and yt-dlp fixes the breakage quickly. The image installs the newest yt-dlp at build time, so rebuild every week or two, or whenever downloads start failing:

```sh
docker compose build --pull && docker compose up -d
```

## Cookies (Instagram / Facebook)

Instagram and Facebook often refuse anonymous downloads. To fix this:

1. Log in with a **throwaway account**, then export its cookies in Netscape format, for example with the "Get cookies.txt LOCALLY" browser extension.
2. Save the file as `secrets/cookies.txt`.
3. Uncomment the `volumes` block in `docker-compose.yml`.
4. Set `COOKIES_FILE=/secrets/cookies.txt` in `.env`.

## Configuration

| Variable         | Default | Meaning                                   |
| ---------------- | ------- | ----------------------------------------- |
| `DISCORD_TOKEN`  | —       | Bot token (required)                      |
| `COOKIES_FILE`   | unset   | Path to a cookies.txt for yt-dlp          |
| `MAX_DURATION`   | `600`   | Skip videos longer than this many seconds |
| `MAX_CONCURRENT` | `2`     | Downloads/encodes allowed at once         |

To support another site, add its domain to `SUPPORTED_DOMAINS` in `src/univid/links.py`.

## Development

```sh
uv run pytest
uv run python -m univid.downloader <url> [max_mb]   # test a download without Discord
```
