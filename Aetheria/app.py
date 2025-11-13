import os
import random
from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime

try:
    import openai
except Exception:
    openai = None


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    # Database path for generated image metadata
    app.config.setdefault('DATABASE', os.path.join(app.root_path, 'generated.db'))

    def init_db():
        db_path = app.config['DATABASE']
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS generated (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                prompt TEXT,
                crystal TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()
        conn.close()

    init_db()

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


    @app.route('/generated')
    def gallery():
        return render_template('generated.html')


    @app.route('/api/generated', methods=['GET'])
    def list_generated():
        # return list of generated images from DB
        db_path = app.config['DATABASE']
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT id, filename, prompt, crystal, created_at FROM generated ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        items = []
        for r in rows:
            items.append({'id': r[0], 'image': '/static/generated/' + r[1], 'prompt': r[2], 'crystal': r[3], 'created_at': r[4]})
        return jsonify({'items': items})


    @app.route('/api/generated/<int:gid>', methods=['DELETE'])
    def delete_generated(gid):
        db_path = app.config['DATABASE']
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT filename FROM generated WHERE id=?', (gid,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'not found'}), 404
        filename = row[0]
        c.execute('DELETE FROM generated WHERE id=?', (gid,))
        conn.commit()
        conn.close()
        # remove file
        path = os.path.join(app.static_folder, 'generated', filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        return jsonify({'deleted': gid})


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
        prompts = data.get('prompts')
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
            # insert metadata into DB
            try:
                conn = sqlite3.connect(app.config['DATABASE'])
                c = conn.cursor()
                c.execute('INSERT INTO generated (filename, prompt, crystal, created_at) VALUES (?,?,?,?)',
                          (fname, prompt, crystal, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
            except Exception:
                pass
            return f'/static/generated/{fname}'

        def save_debug_response(obj, prefix='sd_debug'):
            """Save SD response (JSON or text) to static/sd_debug and return the public path."""
            import json, uuid
            try:
                debug_dir = os.path.join(app.static_folder, 'sd_debug')
                os.makedirs(debug_dir, exist_ok=True)
                fname = f"{prefix}-{uuid.uuid4().hex[:10]}.json"
                out_path = os.path.join(debug_dir, fname)
                # try to dump JSON nicely, fall back to str()
                try:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(obj, f, indent=2, ensure_ascii=False)
                except Exception:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(str(obj))
                return f'/static/sd_debug/{fname}'
            except Exception:
                return None

        # If use_sd, attempt to call local SD API and save returned base64 images
        if use_sd:
            sd_url = os.environ.get('LOCAL_SD_URL', 'http://127.0.0.1:7860/sdapi/v1/txt2img')
            try:
                import requests
                # helper: recursively search JSON-like structure for base64 image strings
                def extract_base64_images(node):
                    found = []
                    if node is None:
                        return found
                    if isinstance(node, str):
                        s = node.strip()
                        if s.startswith('data:image') and 'base64,' in s:
                            found.append(s)
                            return found
                        if len(s) > 800 and all(c.isalnum() or c in '+/=' for c in s[:200]):
                            found.append(s)
                            return found
                        return found
                    if isinstance(node, dict):
                        for k in ('images', 'image', 'result', 'outputs', 'artifacts', 'images_base64'):
                            if k in node:
                                return extract_base64_images(node[k])
                        for v in node.values():
                            found.extend(extract_base64_images(v))
                        return found
                    if isinstance(node, list):
                        for item in node:
                            found.extend(extract_base64_images(item))
                        return found
                    return found

                # helper to extract metadata (seed/steps/sampler) from response
                def extract_metadata(node):
                    md = {}
                    if not node:
                        return md
                    if isinstance(node, dict):
                        for k in ('seed', 'steps', 'sampler', 'sampler_name', 'seed_value', 'cfg_scale'):
                            if k in node:
                                md[k] = node[k]
                        for v in node.values():
                            if isinstance(v, (dict, list)):
                                nested = extract_metadata(v)
                                for kk, vv in nested.items():
                                    if kk not in md:
                                        md[kk] = vv
                    elif isinstance(node, list):
                        for item in node:
                            nested = extract_metadata(item)
                            for kk, vv in nested.items():
                                if kk not in md:
                                    md[kk] = vv
                    return md

                # If a batch of prompts is provided, handle them sequentially and return array of urls
                if prompts and isinstance(prompts, list):
                    results = []
                    # prepare headers once
                    headers = {'Content-Type': 'application/json'}
                    local_key = os.environ.get('LOCAL_SD_KEY')
                    key_header = os.environ.get('LOCAL_SD_KEY_HEADER', 'Authorization')
                    if local_key:
                        if key_header.lower() == 'authorization' and not local_key.lower().startswith('bearer '):
                            headers[key_header] = f'Bearer {local_key}'
                        else:
                            headers[key_header] = local_key

                    # common payload parameters
                    width = int(data.get('width', 512))
                    height = int(data.get('height', 768))
                    steps = int(data.get('steps', 20))
                    sampler = data.get('sampler', None)
                    cfg_scale = float(data.get('cfg_scale', 7.0))
                    samples = int(data.get('samples', 1))
                    seed = data.get('seed', None)
                    negative = data.get('negative_prompt', None)

                    for p in prompts:
                        payload = {
                            'prompt': p,
                            'width': width,
                            'height': height,
                            'steps': steps,
                            'cfg_scale': cfg_scale,
                            'samples': samples,
                        }
                        if sampler:
                            payload['sampler_name'] = sampler
                        if seed is not None:
                            try:
                                payload['seed'] = int(seed)
                            except Exception:
                                payload['seed'] = seed
                        if negative:
                            payload['negative_prompt'] = negative

                        try:
                            r = requests.post(sd_url, json=payload, timeout=60, headers=headers)
                        except Exception as e:
                            results.append({'error': str(e)})
                            continue
                        if r.status_code != 200:
                            results.append({'error': f'sd_status_{r.status_code}', 'body': r.text})
                            continue
                        try:
                            j = r.json()
                        except Exception:
                            j = {'raw_text': r.text}
                        images = extract_base64_images(j)
                        if not images:
                            dbg = save_debug_response(j) if data.get('debug') else None
                            results.append({'error': 'no_images', 'sd_body': j, 'sd_debug_file': dbg})
                            continue
                        # save first image for this prompt
                        url = save_base64_image(images[0], prefix='sd')
                        results.append({'prompt': p, 'image': url, 'meta': extract_metadata(j)})
                    return jsonify({'results': results, 'prompt_batch': len(prompts)})
                # Build a richer payload for common SD REST endpoints (txt2img style).
                # Accept optional parameters from the incoming request to override defaults.
                width = int(data.get('width', 512))
                height = int(data.get('height', 768))
                steps = int(data.get('steps', 20))
                sampler = data.get('sampler', None)
                cfg_scale = float(data.get('cfg_scale', 7.0))
                samples = int(data.get('samples', 1))
                seed = data.get('seed', None)
                negative = data.get('negative_prompt', None)

                payload = {
                    'prompt': prompt,
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'cfg_scale': cfg_scale,
                    'samples': samples,
                }
                if sampler:
                    payload['sampler_name'] = sampler
                if seed is not None:
                    try:
                        payload['seed'] = int(seed)
                    except Exception:
                        payload['seed'] = seed
                if negative:
                    payload['negative_prompt'] = negative
                # support an optional local SD API key (set LOCAL_SD_KEY) and header name (LOCAL_SD_KEY_HEADER)
                headers = {'Content-Type': 'application/json'}
                local_key = os.environ.get('LOCAL_SD_KEY')
                key_header = os.environ.get('LOCAL_SD_KEY_HEADER', 'Authorization')
                if local_key:
                    # if header is Authorization and key doesn't already start with Bearer, add prefix
                    if key_header.lower() == 'authorization' and not local_key.lower().startswith('bearer '):
                        headers[key_header] = f'Bearer {local_key}'
                    else:
                        headers[key_header] = local_key

                r = requests.post(sd_url, json=payload, timeout=30, headers=headers)
                debug = data.get('debug', False)
                if r.status_code == 200:
                    try:
                        j = r.json()
                    except Exception:
                        j = {'raw_text': r.text}
                    # Robust extraction: different SD frontends return images in different shapes.
                    def extract_base64_images(node):
                        """Recursively search JSON-like structure for base64 image strings.
                        Accepts 'data:image/png;base64,...', raw base64, or dict entries like {'b64': '...'}.
                        Returns list of base64 (possibly with data: header) strings.
                        """
                        found = []
                        if node is None:
                            return found
                        if isinstance(node, str):
                            s = node.strip()
                            # common header form
                            if s.startswith('data:image') and 'base64,' in s:
                                found.append(s)
                                return found
                            # raw base64-looking string (heuristic: long and mostly base64 chars)
                            if len(s) > 800 and all(c.isalnum() or c in '+/=' for c in s[:200]):
                                # assume it's base64 image - caller will decode
                                found.append(s)
                                return found
                            return found
                        if isinstance(node, dict):
                            # common keys
                            for k in ('images', 'image', 'result', 'outputs', 'artifacts', 'images_base64'):
                                if k in node:
                                    return extract_base64_images(node[k])
                            for v in node.values():
                                found.extend(extract_base64_images(v))
                            return found
                        if isinstance(node, list):
                            for item in node:
                                found.extend(extract_base64_images(item))
                            return found
                        return found

                    images = extract_base64_images(j)
                    # helper to extract metadata (seed/steps/sampler) from response
                    def extract_metadata(node):
                        md = {}
                        if not node:
                            return md
                        if isinstance(node, dict):
                            for k in ('seed', 'steps', 'sampler', 'sampler_name', 'seed_value', 'cfg_scale'):
                                if k in node:
                                    md[k] = node[k]
                            # many SD frontends include parameters/info under 'info' or within nested dicts
                            for v in node.values():
                                if isinstance(v, (dict, list)):
                                    nested = extract_metadata(v)
                                    for kk, vv in nested.items():
                                        if kk not in md:
                                            md[kk] = vv
                        elif isinstance(node, list):
                            for item in node:
                                nested = extract_metadata(item)
                                for kk, vv in nested.items():
                                    if kk not in md:
                                        md[kk] = vv
                        return md

                    if images and len(images) > 0:
                        result_images = []
                        meta = extract_metadata(j)
                        # Save all found images
                        for idx, img_b64 in enumerate(images):
                            choice = img_b64
                            # prefer data:... if present
                            if isinstance(img_b64, str) and img_b64.startswith('data:'):
                                choice = img_b64
                            url = save_base64_image(choice, prefix=f'sd{idx}')
                            if url:
                                result_images.append({'url': url, 'index': idx})
                        out = {'images': result_images, 'prompt': prompt, 'meta': meta}
                        if debug:
                            out['sd_response'] = j
                        return jsonify(out)
                    else:
                        # No images found in response
                        if debug:
                            # save debug file to static for offline inspection
                            dbg_path = save_debug_response(j)
                            out = {'sd_status': r.status_code, 'sd_body': j}
                            if dbg_path:
                                out['sd_debug_file'] = dbg_path
                            return jsonify(out)
            except Exception as e:
                print('SD call failed or not available:', e)
                if data.get('debug'):
                    dbg_path = save_debug_response({'error': str(e), 'text': str(e)})
                    out = {'error': str(e)}
                    if dbg_path:
                        out['sd_debug_file'] = dbg_path
                    return jsonify(out)

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
