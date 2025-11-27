# 创建一个测试脚本 test_sd_connection.py
import requests
import json


def test_sd_connection():
    try:
        url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
        payload = {
            "prompt": "a beautiful mystical tarot card, fantasy art",
            "steps": 20,
            "width": 512,
            "height": 768
        }

        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ Stable Diffusion连接成功！")
            return True
        else:
            print(f"❌ Stable Diffusion返回错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到Stable Diffusion: {e}")
        return False


if __name__ == "__main__":
    test_sd_connection()