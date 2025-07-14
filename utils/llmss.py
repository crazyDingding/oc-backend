from datetime import datetime
from typing import AsyncGenerator
import os
from modules.texter.text_generator import TextGenerator
from modules.imager.image_generator import ImageGenerator
from utils.utils import extract_value_from_description
import logging
import json
from dotenv import load_dotenv
import requests
from requests import RequestException, ReadTimeout
from tqdm import tqdm

from utils.utils import upload_to_imgbb, convert_image_to_png
import time
import base64
import tempfile
import urllib.request


load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')
DS_API_KEY = os.getenv('DS_API_KEY')
KIMI_API_KEY = os.getenv('KIMI_API_KEY')
VOICE_API_KEY = os.getenv('VOICE_API_KEY')
SD_API_KEY = os.getenv('SD_API_KEY')    
VS_API_KEY = os.getenv('VS_API_KEY')


OPENAI_ORGANIZATION = os.getenv('OPENAI_ORGANIZATION')

BASE_URL = os.getenv('OPENAI_BASE_URL')
CONNECTION_STRING = os.getenv('CONNECTION_STRING')

proxies = {
            "http": os.getenv('HTTP_PROXY'),
            "https": os.getenv('HTTPS_PROXY'),
            "all": os.getenv('ALL_PROXY')
}
# add
MODEL_SERVER = os.getenv('MODEL_SERVER')
class VisionStory:
    """
    VisionStory API 封装，结构风格参考 StableDiffusion。
    支持自定义头像上传、文本/音频生成视频、轮询视频状态。
    """
    def __init__(self, api_key=None, text_generator=None, image_generator=None):
        self.api_key = api_key or os.getenv("VISIONSTORY_API_KEY") or os.getenv("VS_API_KEY")
        
        # 检查API密钥是否存在
        if not self.api_key:
            raise ValueError("VisionStory API key not found. Please set VISIONSTORY_API_KEY or VS_API_KEY environment variable.")
        
        self.headers = {"X-API-Key": self.api_key}
        self.video_url = "https://openapi.visionstory.ai/api/v1/video"
        self.avatar_url = "https://openapi.visionstory.ai/api/v1/avatar"
        
        print(f"[VisionStory] Initialized with API key: {self.api_key[:10]}...")
        
        if text_generator is None:
            self.text_generator = TextGenerator()
        else:
            self.text_generator = text_generator
        if image_generator is None:
            self.image_generator = ImageGenerator()
        else:
            self.image_generator = image_generator

    def encode_base64(self, file_path):
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # 下载到临时文件
            with urllib.request.urlopen(file_path) as response:
                data = response.read()
            return base64.b64encode(data).decode('utf-8')
        else:
            with open(file_path, 'rb') as file:
                return base64.b64encode(file.read()).decode('utf-8')

    def get_mime_type(self, image_path):
        ext = os.path.splitext(image_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            return "image/jpeg"
        elif ext == ".png":
            return "image/png"
        else:
            return "application/octet-stream"

    def test_api_key(self):
        """测试API密钥是否有效"""
        try:
            # 尝试访问一个简单的API端点来验证密钥
            test_url = "https://openapi.visionstory.ai/api/v1/avatar"
            resp = requests.get(test_url, headers=self.headers)
            print(f"[VisionStory] API key test response: {resp.status_code}")
            if resp.status_code == 200:
                print("[VisionStory] API key is valid")
                return True
            elif resp.status_code == 401:
                print("[VisionStory] API key is invalid (401 Unauthorized)")
                return False
            elif resp.status_code == 403:
                print("[VisionStory] API key is invalid (403 Forbidden)")
                return False
            else:
                print(f"[VisionStory] Unexpected response: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[VisionStory] Error testing API key: {e}")
            return False

    def upload_avatar(self, image_path, name="Custom Avatar"):
        # 首先测试API密钥
        if not self.test_api_key():
            raise ValueError("VisionStory API key is invalid. Please check your API key.")
        
        payload = {
            "inline_data": {
                "mime_type": self.get_mime_type(image_path),
                "data": self.encode_base64(image_path)
            },
            "name": name
        }
        
        print(f"[VisionStory] Uploading avatar: {name}")
        print(f"[VisionStory] Image path: {image_path}")
        print(f"[VisionStory] Headers: {self.headers}")
        
        try:
            resp = requests.post(self.avatar_url, json=payload, headers=self.headers)
            print(f"[VisionStory] Upload avatar response: {resp.status_code}")
            print(f"[VisionStory] Response text: {resp.text}")
            
            if resp.status_code == 403:
                print(f"[VisionStory] 403 Forbidden - API key may be invalid or expired")
                print(f"[VisionStory] Current API key: {self.api_key[:10]}...")
                print(f"[VisionStory] Please check:")
                print(f"[VisionStory] 1. API key is correct")
                print(f"[VisionStory] 2. API key has proper permissions")
                print(f"[VisionStory] 3. Account has sufficient credits")
            
            resp.raise_for_status()
            return resp.json()["data"]["avatar_id"]
        except requests.exceptions.HTTPError as e:
            print(f"[VisionStory] HTTP Error: {e}")
            raise
        except Exception as e:
            print(f"[VisionStory] Unexpected error: {e}")
            raise

    def generate_video_with_text(self, text, *, voice_id="Alice", model_id="vs_talk_v1", avatar_id, aspect_ratio, resolution):
        """
        生成视频，avatar_id、aspect_ratio、resolution 必须显式传入。
        :param text: 文本内容
        :param voice_id: 声音ID
        :param model_id: 模型ID
        :param avatar_id: VisionStory上传头像后返回的ID（必填）
        :param aspect_ratio: 比例（如 '9:16'）（必填）
        :param resolution: 分辨率（如 '480p'）（必填）
        :return: video_id
        """
        payload = {
            "model_id": model_id,
            "avatar_id": avatar_id,
            "text_script": {
                "text": text,
                "voice_id": voice_id
            },
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }
        resp = requests.post(self.video_url, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()["data"]["video_id"]

    def generate_video_with_audio(self, audio_path, voice_id="Alice", model_id="vs_talk_v1", avatar_id="4321918387609092991", aspect_ratio="9:16", resolution="480p"):
        payload = {
            "model_id": model_id,
            "avatar_id": avatar_id,
            "audio_script": {
                "inline_data": {
                    "mime_type": "audio/mp3",
                    "data": self.encode_base64(audio_path)
                },
                "voice_change": True,
                "voice_id": voice_id,
                "denoise": True
            },
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }
        resp = requests.post(self.video_url, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()["data"]["video_id"]

    def poll_video_status(self, video_id, timeout=120):
        wait_time = 0
        while wait_time <= timeout:
            time.sleep(5)
            wait_time += 5
            try:
                params = {"video_id": video_id}
                resp = requests.get(self.video_url, params=params, headers=self.headers)
                resp.raise_for_status()
                resp_json = resp.json()
                data = resp_json.get("data", {})
                status = data.get("status", "")
                if status == "created":
                    return data
                print(f"[Polling] Waiting for video_id {video_id}... status = {status}")
            except Exception as e:
                print(f"[Polling Error] {str(e)}")
        raise TimeoutError("Video generation timed out.")

    def generate_video_from_prompt(self, dialogues, description, avatar_name="Custom Avatar"):
        """
        自动：文本生成->图片生成->上传avatar->生成视频->轮询
        :param dialogues: 用于生成文本的对话输入 List[Dict[str, str]]
        :param description: 角色描述 List[dict]
        :param avatar_name: 上传avatar的名字
        :return: dict, 包含 video_url, avatar_id, text, image_path
        """
        # ==== 超参数配置====
        aspect_ratio = "9:16"
        resolution = "720p"
        voice_id = "Alice"
        model_id = "vs_talk_v1"
        # ======================================
        # 1. 生成文本
        text = self.text_generator.generate_text_stream(dialogues, description)
        # 2. 生成图片
        image_path, _ = self.image_generator.generate_image(description=description)
        if not image_path:
            raise RuntimeError("Image generation failed, cannot proceed to upload avatar.")
        # 3. 上传avatar
        avatar_id = self.upload_avatar(image_path, name=avatar_name)
        # 4. 生成视频
        video_id = self.generate_video_with_text(
            text=text,
            avatar_id=avatar_id,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            voice_id=voice_id,
            model_id=model_id
        )
        # 5. 轮询
        video_data = self.poll_video_status(video_id)
        return {
            "video_url": video_data.get("video_url"),
            "avatar_id": avatar_id,
            "text": text,
            "image_path": image_path
        }
def test_vedio_generate():
    """
    本地测试 VisionStory 自动视频生成流程。
    """
    visionstory = VisionStory()
    # 示例 dialogues 和 description
    dialogues = [
        {"Input": "你好，今天过得怎么样？"}
    ]
    description = [
        {"Name": "Airi"},
        {"Gender": "Female"},
        {"Personality": "Gentle"},
        {"Appearance": "long silver hair, blue eyes, elegant dress"}
    ]
    avatar_name = "Airi"
    print("[TEST] 开始自动生成视频...")
    result = visionstory.generate_video_from_prompt(dialogues, description, avatar_name=avatar_name)
    print("[TEST] 生成结果：")
    print("video_url:", result.get("video_url"))
    print("avatar_id:", result.get("avatar_id"))
    print("text:", result.get("text"))
    print("image_path:", result.get("image_path"))

if __name__ == "__main__":
    test_vedio_generate()
# ... existing code ...
