import os
import random
from flask import Flask, render_template, jsonify, request

try:
    import openai
except Exception:
    openai = None


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Minimal in-memory deck (major arcana subset for demo)
    DECK = [
        {"name": "The Fool", "meaning": "New beginnings, spontaneity, a leap of faith.", "image": "/static/images/cards/the_fool.svg"},
        {"name": "The Magician", "meaning": "Skill, resourcefulness, the power to manifest.", "image": "/static/images/cards/the_magician.svg"},
        {"name": "The High Priestess", "meaning": "Intuition, inner knowledge, mystery.", "image": "/static/images/cards/the_high_priestess.svg"},
        {"name": "The Empress", "meaning": "Fertility, creativity, abundance.", "image": "/static/images/cards/the_empress.svg"},
        {"name": "The Emperor", "meaning": "Structure, authority, leadership.", "image": "/static/images/cards/the_emperor.svg"},
        {"name": "The Hierophant", "meaning": "Tradition, learning, spiritual guidance."},
        {"name": "The Lovers", "meaning": "Relationships, choices, harmony."},
        {"name": "The Chariot", "meaning": "Willpower, success through determination."},
        {"name": "Strength", "meaning": "Courage, patience, inner strength."},
        {"name": "The Hermit", "meaning": "Solitude, inner search, wisdom."},
        {"name": "Wheel of Fortune", "meaning": "Cycles, destiny, turning points."},
        {"name": "Justice", "meaning": "Fairness, truth, law."},
        {"name": "The Hanged Man", "meaning": "Surrender, new perspective."},
        {"name": "Death", "meaning": "Transformation, endings and beginnings."},
        {"name": "Temperance", "meaning": "Balance, moderation, healing."},
        {"name": "The Devil", "meaning": "Attachments, shadow, temptation."},
        {"name": "The Tower", "meaning": "Disruption, sudden change, revelation."},
        {"name": "The Star", "meaning": "Hope, inspiration, renewal."},
        {"name": "The Moon", "meaning": "Illusion, subconscious, emotions."},
        {"name": "The Sun", "meaning": "Joy, success, vitality."},
        {"name": "Judgement", "meaning": "Awakening, rebirth, evaluation."},
        {"name": "The World", "meaning": "Completion, wholeness, travel."},
    ]


    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/api/cards', methods=['POST'])
    def cards():
        data = request.json or {}
        reading = data.get('reading', 'single')
        crystal = data.get('crystal')

        counts = {'single': 1, 'three': 3, 'five': 5}
        num = counts.get(reading, 1)
        picked = random.sample(DECK, k=num)

        # add reversed randomly for flavor
        for c in picked:
            c['reversed'] = random.choice([False, False, True])

        response = {
            'crystal': crystal,
            'reading': reading,
            'cards': picked,
            'message': f'A {reading} card reading using {crystal or "your chosen crystal"}.'
        }
        return jsonify(response)


    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.json or {}
        msg = data.get('message', '')
        crystal = data.get('crystal')

        # If OpenAI key is available and openai package is installed, use it.
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai and openai_key:
            try:
                openai.api_key = openai_key
                # small prompt that keeps things light and mystical
                prompt = (
                    "You are a friendly fortune-teller bot. Respond helpfully and briefly. "
                    f"User message: {msg}"
                )
                completion = openai.Completion.create(
                    engine=os.environ.get('OPENAI_ENGINE', 'text-davinci-003'),
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.9,
                )
                text = completion.choices[0].text.strip()
                return jsonify({'reply': text})
            except Exception as e:
                # fall through to local responder
                print('OpenAI call failed:', e)

        # Local simple rule-based reply when no API key
        fallback_replies = [
            "I sense a change approaching — be open and stay curious.",
            "Follow your intuition today; a small choice will lead somewhere meaningful.",
            "The crystal's glow points to new connections shortly.",
            "Take a breath. A clear head will reveal the right next step.",
            "Trust the small signals — they add up to big answers.",
        ]

        # sprinkle in parts of the user's message for perceived relevance
        if msg:
            if 'love' in msg.lower():
                reply = "Love is in flux — honest communication will guide you."
            elif 'work' in msg.lower() or 'career' in msg.lower():
                reply = "At work, steady focus wins. Consider which task needs your clarity." 
            else:
                reply = random.choice(fallback_replies)
        else:
            reply = random.choice(fallback_replies)

        return jsonify({'reply': reply})


    @app.route('/api/generate', methods=['POST'])
    def generate():
        """Generate an image for a visual prompt. If USE_SD=true, this would proxy to a local Stable Diffusion service.
        For safety in this demo, we return a bundled placeholder image and echo the prompt.
        """
        data = request.json or {}
        prompt = data.get('prompt', '')
        crystal = data.get('crystal')

        use_sd = os.environ.get('USE_SD', 'false').lower() == 'true'

        def save_base64_image(b64data, prefix='gen'):
            import base64, uuid
            header = ''
            if b64data.startswith('data:'):
                header, b64data = b64data.split(',', 1)
            try:
                data = base64.b64decode(b64data)
            except Exception:
                return None
            fname = f"{prefix}-{uuid.uuid4().hex[:12]}.png"
            out_path = os.path.join(app.static_folder, 'generated', fname)
            with open(out_path, 'wb') as f:
                f.write(data)
            return f'/static/generated/{fname}'

        # If use_sd, attempt to call local SD API and save returned base64 images
        if use_sd:
            sd_url = os.environ.get('LOCAL_SD_URL', 'http://127.0.0.1:7860/sdapi/v1/txt2img')
            try:
                import requests
                payload = { 'prompt': prompt }
                r = requests.post(sd_url, json=payload, timeout=30)
                debug = data.get('debug', False)
                if r.status_code == 200:
                    try:
                        j = r.json()
                    except Exception:
                        j = {'raw_text': r.text}
                    # Many SD web UIs return 'images' array of base64 strings
                    images = None
                    if isinstance(j, dict):
                        images = j.get('images') or j.get('result') or None
                    if images and isinstance(images, list) and len(images) > 0:
                        url = save_base64_image(images[0], prefix='sd')
                        if url:
                            out = {'image': url, 'prompt': prompt}
                            if debug:
                                out['sd_response'] = j
                            return jsonify(out)
                    else:
                        # No images found in response
                        if debug:
                            return jsonify({'sd_status': r.status_code, 'sd_body': j})
            except Exception as e:
                print('SD call failed or not available:', e)
                if data.get('debug'):
                    return jsonify({'error': str(e)})

        # Also accept direct base64 image in the request body under 'image'
        incoming_image = data.get('image')
        if incoming_image:
            url = save_base64_image(incoming_image, prefix='upload')
            if url:
                return jsonify({'image': url, 'prompt': prompt})

        # Fallback: return a bundled placeholder
        return jsonify({'image': '/static/images/cards/the_fool.svg', 'prompt': prompt})


    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
