# AI Fortune Teller (Flask)

This is a small demo Flask app that provides an interactive AI fortune-telling experience. Users can pick a crystal, draw tarot-like cards, and chat with a fortune-teller chatbot.

Features:
- Crystal selection
- Single/Three/Five card readings
- Chat endpoint with optional OpenAI integration (uses OPENAI_API_KEY environment variable)

Quick start:

1. Create a virtualenv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app

```bash
export FLASK_APP=app.py
flask run
```

3. Open http://127.0.0.1:5000 in your browser.

Optional OpenAI integration:
Set the environment variable OPENAI_API_KEY. The app will attempt to use the key and the package `openai` to give richer chat responses. If none is present, the app uses a small local fallback.

Follow-ups & improvements:
- Add user sessions and persistent readings
- Better card artwork and animations
- Use streaming chat for more natural bot replies
