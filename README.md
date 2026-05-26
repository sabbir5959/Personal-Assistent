# Sabbir Personal AI

A single-file browser GUI personal assistant powered by Gemini.

## Run locally

Create `.env`:

```bash
cp .env.example .env
```

Put your Gemini API key in `.env`, then run:

```bash
python3 personal_ai_bot.py
```

## Give friends a link

Deploy it to a Python hosting service such as Render.

1. Upload this folder to a GitHub repository.
2. Do not upload `.env`; `.gitignore` already protects it.
3. On Render, create a new Web Service from the GitHub repo.
4. Use this start command:

```bash
HOST=0.0.0.0 NO_BROWSER=1 python3 personal_ai_bot.py
```

5. Add environment variables in Render:

```bash
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash
```

Render will give you a public URL. Send that URL to your friends.

## Important

If you use your own Gemini API key on the server, your friends' usage may count against your quota or billing.
