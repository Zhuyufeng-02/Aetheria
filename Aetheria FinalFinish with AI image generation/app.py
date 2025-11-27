import os
import random
import math
from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests
from comfyui_run import queue_workflow_and_wait
try:
    import openai
except Exception:
    openai = None


class PILImageGenerator:
    def __init__(self):
        self.colors = {
            'mystical': ['#6A0DAD', '#8A2BE2', '#9370DB', '#BA55D3'],
            'earth': ['#8B4513', '#A0522D', '#CD853F', '#D2691E'],
            'water': ['#1E90FF', '#00BFFF', '#87CEEB', '#4682B4'],
            'fire': ['#FF4500', '#FF6347', '#DC143C', '#B22222'],
            'air': ['#F0F8FF', '#E6E6FA', '#D8BFD8', '#DDA0DD']
        }

    def generate_tarot_image(self, card_name, meaning, width=512, height=768):
        """生成塔罗牌风格的图像"""
        # 创建画布
        image = Image.new('RGB', (width, height), color=self._get_background_color(card_name))
        draw = ImageDraw.Draw(image)

        # 添加装饰性边框
        self._draw_border(draw, width, height)

        # 添加中心符号
        self._draw_central_symbol(draw, card_name, width, height)

        # 添加卡片名称
        self._draw_text(draw, card_name, width, height // 4, is_title=True)

        # 添加含义（简短的）
        short_meaning = meaning.split('。')[0] if '。' in meaning else meaning[:30]
        self._draw_text(draw, short_meaning, width, height * 3 // 4, is_title=False)

        # 添加神秘的光晕效果
        self._draw_glow_effects(draw, width, height)

        return self._image_to_base64(image)

    def generate_crystal_ball_image(self, prompt, width=512, height=512):
        """生成水晶球图像"""
        image = Image.new('RGB', (width, height), color='#2F1B4D')
        draw = ImageDraw.Draw(image)

        # 绘制水晶球
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3

        # 水晶球外圈
        draw.ellipse([center_x - radius, center_y - radius,
                      center_x + radius, center_y + radius],
                     fill='#4B0082', outline='#9370DB', width=3)

        # 水晶球内圈（半透明效果）
        inner_radius = radius - 10
        for i in range(5):
            r = inner_radius - i * 5
            alpha = 100 - i * 20
            color = self._adjust_alpha('#8A2BE2', alpha)
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r],
                         fill=color)

        # 添加闪光点
        for _ in range(20):
            x = center_x + random.randint(-inner_radius, inner_radius)
            y = center_y + random.randint(-inner_radius, inner_radius)
            if (x - center_x) ** 2 + (y - center_y) ** 2 <= inner_radius ** 2:
                size = random.randint(2, 5)
                draw.ellipse([x - size, y - size, x + size, y + size], fill='white')

        # 添加文字
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        text = f"🔮 {prompt[:40]}..."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((width // 2 - text_width // 2, height - 40), text, fill='white', font=font)

        return self._image_to_base64(image)

    def generate_fortune_image(self, prompt, width=512, height=512):
        """生成通用占卜图像"""
        # image = Image.new('RGB', (width, height), color='#1A1A2E')
        # draw = ImageDraw.Draw(image)

        # # 绘制星空背景
        # for _ in range(100):
        #     x = random.randint(0, width)
        #     y = random.randint(0, height)
        #     size = random.randint(1, 3)
        #     brightness = random.randint(150, 255)
        #     draw.ellipse([x, y, x + size, y + size], fill=(brightness, brightness, brightness))

        # use comfyui to generate the image 
        image_url = queue_workflow_and_wait(prompt=prompt, width=width, height=height)
        response = requests.get(image_url)
        image = Image.open(io.BytesIO(response.content)).convert('RGB')
        
        # Update width and height to match the actual generated image
        width, height = image.size
        
        draw = ImageDraw.Draw(image)

        # # 绘制神秘符号
        center_x, center_y = width // 2, height // 2
        symbols = ['✧', '✦', '✶', '✺', '✹']

        try:
            font = ImageFont.truetype("seguiemj.ttf", 60)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()

        for i, symbol in enumerate(symbols):
            angle = i * (360 / len(symbols))
            rad = math.radians(angle)
            distance = 100
            x = center_x + distance * math.cos(rad)
            y = center_y + distance * math.sin(rad)

            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            draw.text((x - text_width // 2, y - text_height // 2),
                      symbol, fill='#E94560', font=font)

        # 添加提示文字
        try:
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            small_font = ImageFont.load_default()

        text_lines = self._wrap_text(prompt, small_font, width - 40)
        for i, line in enumerate(text_lines):
            bbox = draw.textbbox((0, 0), line, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text((width // 2 - text_width // 2, height - 60 - i * 20),
                      line, fill='#FFFFFF', font=small_font)

        return self._image_to_base64(image)

    def _get_background_color(self, card_name):
        """根据卡片名称获取背景颜色"""
        color_groups = list(self.colors.values())
        return random.choice(random.choice(color_groups))

    def _draw_border(self, draw, width, height):
        """绘制装饰性边框"""
        # 外边框
        border_width = 15
        draw.rectangle([0, 0, width, height], outline='gold', width=border_width)

        # 内边框
        inner_border = 30
        draw.rectangle([inner_border, inner_border, width - inner_border, height - inner_border],
                       outline='silver', width=2)

    def _draw_central_symbol(self, draw, card_name, width, height):
        """绘制中心符号"""
        center_x, center_y = width // 2, height // 2
        symbols = ['★', '☆', '☾', '☀', '♡', '◇', '♤', '♧']
        symbol = random.choice(symbols)

        # 绘制符号
        try:
            font = ImageFont.truetype("seguiemj.ttf", 80)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), symbol, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.text((center_x - text_width // 2, center_y - text_height // 2),
                  symbol, fill='gold', font=font)

    def _draw_text(self, draw, text, width, y_pos, is_title=True):
        """绘制文本"""
        try:
            if is_title:
                font = ImageFont.truetype("arial.ttf", 28)
            else:
                font = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        color = 'gold' if is_title else 'silver'
        draw.text((width // 2 - text_width // 2, y_pos), text, fill=color, font=font)

    def _draw_glow_effects(self, draw, width, height):
        """绘制光晕效果"""
        center_x, center_y = width // 2, height // 2
        for i in range(3):
            radius = 100 + i * 30
            alpha = 30 - i * 10
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x = center_x + radius * math.cos(rad)
                y = center_y + radius * math.sin(rad)
                size = 5 + i * 2
                draw.ellipse([x - size, y - size, x + size, y + size], fill='white')

    def _adjust_alpha(self, color, alpha):
        """调整颜色透明度（模拟）"""
        return color

    def _wrap_text(self, text, font, max_width):
        """将文本换行以适应宽度"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines[:3]  # 最多返回3行

    def _image_to_base64(self, image):
        """将PIL图像转换为base64字符串"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"


# 初始化图像生成器
pil_generator = PILImageGenerator()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    # Database path for generated image metadata
    app.config.setdefault('DATABASE', os.path.join(app.root_path, 'generated.db'))

    def init_db():
        db_path = app.config['DATABASE']
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
                  CREATE TABLE IF NOT EXISTS generated
                  (
                      id
                      INTEGER
                      PRIMARY
                      KEY
                      AUTOINCREMENT,
                      filename
                      TEXT
                      NOT
                      NULL,
                      prompt
                      TEXT,
                      crystal
                      TEXT,
                      created_at
                      TEXT
                  )
                  ''')
        conn.commit()
        conn.close()

    init_db()

    # 确保生成的图片目录存在
    generated_dir = os.path.join(app.static_folder, 'generated')
    os.makedirs(generated_dir, exist_ok=True)

    # Minimal in-memory deck (major arcana subset for demo)
    DECK = [
        {"name": "The Fool", "meaning": "New beginnings, spontaneity, a leap of faith.",
         "image": "/static/images/cards/the_fool.svg"},
        {"name": "The Magician", "meaning": "Skill, resourcefulness, the power to manifest.",
         "image": "/static/images/cards/the_magician.svg"},
        {"name": "The High Priestess", "meaning": "Intuition, inner knowledge, mystery.",
         "image": "/static/images/cards/the_high_priestess.svg"},
        {"name": "The Empress", "meaning": "Fertility, creativity, abundance.",
         "image": "/static/images/cards/the_empress.svg"},
        {"name": "The Emperor", "meaning": "Structure, authority, leadership.",
         "image": "/static/images/cards/the_emperor.svg"},
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
            items.append(
                {'id': r[0], 'image': '/static/generated/' + r[1], 'prompt': r[2], 'crystal': r[3], 'created_at': r[4]})
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
                    engine=os.environ.get('OPENAI_ENGINE', 'text-daventi-003'),
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

    def save_base64_image(b64data, prefix='pil'):
        """保存base64图像到文件系统"""
        # 移除data:image/png;base64,前缀
        if b64data.startswith('data:image'):
            b64data = b64data.split(',', 1)[1]

        try:
            image_binary = base64.b64decode(b64data)
        except Exception as e:
            print(f"Base64解码失败: {e}")
            return None

        # 生成唯一文件名
        import uuid
        fname = f"{prefix}-{uuid.uuid4().hex[:12]}.png"
        out_path = os.path.join(app.static_folder, 'generated', fname)

        # 确保目录存在
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        # 保存图像文件
        with open(out_path, 'wb') as f:
            f.write(image_binary)

        # 插入元数据到数据库
        try:
            conn = sqlite3.connect(app.config['DATABASE'])
            c = conn.cursor()
            c.execute('INSERT INTO generated (filename, prompt, crystal, created_at) VALUES (?,?,?,?)',
                      (fname, "Generated Image", "default", datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            print(f"✅ 图像保存成功: {fname}")
        except Exception as e:
            print(f"数据库保存失败: {e}")

        return f'/static/generated/{fname}'

    @app.route('/api/generate', methods=['POST'])
    def generate():
        """Generate an image using PIL"""
        data = request.json or {}
        prompt = data.get('prompt', 'A mystical vision')
        crystal = data.get('crystal', 'default')
        width = data.get('width', 512)
        height = data.get('height', 1080)

        print(f"🎨 收到生成请求: {prompt}")

        # 使用PIL生成图像
        try:
            # 强制使用 ComfyUI 生成通用占卜图像
            print("✨ 生成通用占卜图像 (ComfyUI)")
            image_data = pil_generator.generate_fortune_image(prompt, width, height)

            # 保存图像到文件系统
            url = save_base64_image(image_data)

            if url:
                print(f"✅ 图像生成成功: {url}")
                return jsonify({
                    'image': url,
                    'prompt': prompt,
                    'note': 'Generated with PIL Image Generator',
                    'type': 'pil_generated',
                    'success': True
                })
            else:
                print("❌ 图像保存失败")
                return jsonify({
                    'image': '/static/images/card-back.png',
                    'prompt': prompt,
                    'note': 'Failed to save generated image',
                    'success': False
                })

        except Exception as e:
            print(f"❌ PIL图像生成失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'image': '/static/images/card-back.png',
                'prompt': prompt,
                'note': f'Image generation failed: {str(e)}',
                'success': False
            }), 500

    @app.route('/api/test_pil_generation')
    def test_pil_generation():
        """测试PIL图像生成"""
        try:
            # 测试塔罗牌生成
            tarot_image = pil_generator.generate_tarot_image(
                "The Fool",
                "New beginnings, spontaneity, a leap of faith."
            )

            # 测试水晶球生成
            crystal_image = pil_generator.generate_crystal_ball_image(
                "A mystical vision of the future"
            )

            # 测试通用占卜图像生成
            fortune_image = pil_generator.generate_fortune_image(
                "Your destiny awaits among the stars"
            )

            return jsonify({
                'status': 'success',
                'message': 'PIL image generation is working',
                'tarot_sample': tarot_image[:100] + '...' if tarot_image else None,
                'crystal_sample': crystal_image[:100] + '...' if crystal_image else None,
                'fortune_sample': fortune_image[:100] + '...' if fortune_image else None
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'PIL generation failed: {str(e)}'
            }), 500

    @app.route('/api/health')
    def health_check():
        """健康检查端点"""
        return jsonify({
            'status': 'healthy',
            'service': 'Aetheria Image Generation',
            'timestamp': datetime.utcnow().isoformat()
        })

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)