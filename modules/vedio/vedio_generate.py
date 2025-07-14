import os
import time
import base64
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from modules.texter.text_generator import TextGenerator
from modules.imager.image_generator import ImageGenerator
from utils.llmss import VisionStory

VEDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../assets/vedio'))
os.makedirs(VEDIO_DIR, exist_ok=True)

# VisionStory API Key
VS_API_KEY = os.getenv('VS_API_KEY')
VISIONSTORY_API_URL = "https://openapi.visionstory.ai/api/v1/video"
HEADERS = {"X-API-Key": VS_API_KEY}

app = FastAPI(title="Video Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

text_gen = TextGenerator()
image_gen = ImageGenerator(mode="text2img")
visionstory = VisionStory(text_generator=text_gen, image_generator=image_gen)

class Text2VedioRequest(BaseModel):
    text: str
    avatar_id: str
    aspect_ratio: str
    resolution: str
    voice_id: str = "Alice"
    model_id: str = "vs_talk_v1"

class AutoVedioRequest(BaseModel):
    dialogues: list
    description: list
    avatar_name: str = "Custom Avatar"

@app.post("/generate/auto_text2vedio")
async def auto_text2vedio(req: AutoVedioRequest):
    """
    自动生成台词、图片，上传avatar，并用VisionStory生成视频
    """
    try:
        result = visionstory.generate_video_from_prompt(req.dialogues, req.description, avatar_name=req.avatar_name)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/generate/voice2vedio")
async def generate_voice2vedio(
    audio: UploadFile = File(...),
    output_filename: Optional[str] = Form(None)
):
    """
    用上传的音频生成视频（VisionStory API）。
    """
    try:
        # 保存音频
        audio_path = os.path.join(VEDIO_DIR, f"temp_audio_{int(time.time())}.mp3")
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

        # 提交生成任务
        video_id = visionstory.generate_video_with_audio(audio_path)
        # 轮询获取视频
        video_data = visionstory.poll_video_status(video_id)
        video_url = video_data["video_url"]

        # 清理临时文件
        os.remove(audio_path)

        return {"video_url": video_url}
    except Exception as e:
        return {"error": str(e)}

@app.post("/generate/text2vedio")
async def generate_text2vedio(req: Text2VedioRequest):
    try:
        video_id = visionstory.generate_video_with_text(
            text=req.text,
            avatar_id=req.avatar_id,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            voice_id=req.voice_id,
            model_id=req.model_id
        )
        video_data = visionstory.poll_video_status(video_id)
        video_url = video_data["video_url"]
        return {"video_url": video_url}
    except Exception as e:
        return {"error": str(e)}

def test_vedio_generate():
    """
    本地测试 VisionStory 自动视频生成流程。
    """
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
