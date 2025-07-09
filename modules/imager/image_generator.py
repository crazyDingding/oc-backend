import os
import sys
import json
from uuid import uuid4
from typing import Optional, List, Tuple

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from flask import Request
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llms import StableDiffusion
from utils.utils import extract_value_from_description, upload_to_imgbb, convert_image_to_png

class ImageGenerator:
    def __init__(self, mode: str = "text2img"):
        self.mode = mode
        self.sd = StableDiffusion(mode=mode)

    def generate_image(
        self,
        description: Optional[List[dict]] = None,
        character_name: Optional[str] = None,
        init_image_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        # —— 1. description 已由外部轮换池准备，直接使用 ——
        if not description:
            print("❌ 缺少角色描述，终止生成")
            return None, "unknown"

        # —— 2. 提取角色名（若未提供） ——
        if not character_name:
            for item in description:
                if "Name" in item and isinstance(item["Name"], str):
                    character_name = item["Name"]
                    break
            if not character_name:
                character_name = "unknown"
            print("📌 提取角色名为：", character_name)

        # —— 3. 构建 prompt ——
        prompt = self.sd.build_front_facing_prompt(description)

        # —— 4. img2img 特有流程 ——
        if self.mode == "img2img":
            if not init_image_path or not os.path.exists(init_image_path):
                print("❌ init_image_path 无效或未提供，无法进行 img2img")
                return None
            # TODO：新建一个用来储存coverted的文件夹
            print(f"🖼️ 转换图像为 PNG：{init_image_path}")
            png_path = convert_image_to_png(init_image_path)

            print(f"📤 上传图像到 imgbb：{png_path}")
            init_image_url = upload_to_imgbb(png_path)
            if not init_image_url:
                print("❌ 上传失败，无法继续 img2img")
                return None

            print("🌐 上传成功，URL:", init_image_url)
        else:
            init_image_url = None

        # —— 5. 调用 StableDiffusion 生成 ——
        print(f"🎨 开始生成 [{self.mode}] 图像，角色：{character_name}")
        remote_url = self.sd.generate(
            prompt=prompt,
            character_name=character_name,
            init_image_url=init_image_url,
            output_path=output_path
        )

        if remote_url:
            print("✅ 图像保存成功：", remote_url)
        else:
            print("❌ 图像生成失败")

        return remote_url, character_name


# —— FastAPI 应用部分 ——

app = FastAPI(title="Image Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# —— 1️⃣ 挂载静态目录，让 /assets/** 直连文件系统 assets/**
# 假设你项目根目录下有 assets/images/*.jpg 及 assets/audios/*.mp3
# app.mount(
#     "/assets",
#     StaticFiles(directory=os.path.join(os.getcwd(), "assets")),
#     name="assets"
# )
#
# class Text2ImgRequest(BaseModel):
#     description: List[dict]
#     character_name: Optional[str] = None
#
#
# @app.post("/generate/text2img")
# def generate_text2img(request: Text2ImgRequest, req: Request):
#     gen = ImageGenerator(mode="text2img")
#     remote_url  = gen.generate_image(
#         description=request.description,
#         character_name=request.character_name
#     )
#     if not remote_url:
#         return {"error": "生成失败"}
#
#     return {
#         "character_name": request.character_name or extract_value_from_description(request.description),
#         "image_url": remote_url  # 返回真实远程链接
#     }
#
#
# @app.post("/generate/img2img")
# async def generate_img2img(
#     description: str = Form(...),
#     file: UploadFile = File(...),
#     character_name: Optional[str] = Form(None),
#     req: Request = None
# ):
#     # —— 解析 description JSON 并处理默认 ——
#     try:
#         desc_list = json.loads(description)
#     except Exception:
#         print("⚠️ description 格式错误，使用默认值")
#         desc_list = DEFAULT_DESCRIPTION
#     if not desc_list or desc_list == []:
#         print("⚠️ description 为空，使用默认值")
#         desc_list = DEFAULT_DESCRIPTION
#
#     # —— 保存前端上传的文件 ——
#     upload_dir = os.path.join(os.getcwd(), "temp_uploads")
#     os.makedirs(upload_dir, exist_ok=True)
#     tmp_path = os.path.join(upload_dir, f"upload_{uuid4().hex}.png")
#     with open(tmp_path, "wb") as f:
#         f.write(await file.read())
#
#     # —— 调用 ImageGenerator ——
#     gen = ImageGenerator(mode="img2img")
#     remote_url = gen.generate_image(
#         description=desc_list,
#         character_name=character_name,
#         init_image_path=tmp_path
#     )
#     if not remote_url:
#         return {"error": "生成失败"}
#
#
#     return {
#         "character_name": character_name or extract_value_from_description(desc_list),
#         "image_url": remote_url  # 返回真实远程链接
#     }

if __name__ == '__main__':
    import asyncio
    from tools.character.manager import CharacterPromptManager
    from utils.redis import r  # 你已有的 Redis 实例

    from modules.imager.image_generator import ImageGenerator

    # 模拟用户信息
    user_id = 87
    description_raw = "0"  # 非法值，触发默认角色轮换机制

    # 初始化角色轮换器
    manager = CharacterPromptManager(user_id=user_id, redis_client=r)
    description = manager.get_character_description(description_raw)
    character_name = manager._extract_name(description)

    # ——— 测试 text2img 模式 ———
    print("\n===== 测试 text2img 模式 =====")
    gen_t2i = ImageGenerator(mode="text2img")
    try:
        url_t2i, name_t2i = gen_t2i.generate_image(
            description=description,
            character_name=character_name
        )
        print("✅ [RESPONSE text2img] Image URL:", url_t2i)
        print("📌 使用角色名：", name_t2i)
    except Exception as e:
        print("❌ [ERROR text2img]", e)

    # ——— 测试 img2img 模式 ———
    print("\n===== 测试 img2img 模式 =====")
    SAMPLE_JPG = "/Users/dingdingdingdingding/Desktop/HKU/sem2/SmartPhone/project/final project1/final project/assets/images/sample_input.jpg"
    gen_i2i = ImageGenerator(mode="img2img")
    try:
        url_i2i, name_i2i = gen_i2i.generate_image(
            description=description,
            character_name=character_name,
            init_image_path=SAMPLE_JPG
        )
        print("✅ [RESPONSE img2img] Image URL:", url_i2i)
        print("📌 使用角色名：", name_i2i)
    except Exception as e:
        print("❌ [ERROR img2img]", e)