import os
import json
import pytest
import time
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from database.database import SessionLocal
from modules.character.models import Character
from modules.imager.models import Image
import modules.character.models
import modules.users.models
import modules.imager.models

client = TestClient(app)

# 全局变量
token = None
user_id = None
character_id = None
mock_redis_store = {}

# ✅ 替换 Redis 的 setex/get/delete
@pytest.fixture(autouse=True)
def mock_redis_methods():
    mock_r = MagicMock()
    mock_r.setex.side_effect = lambda key, ttl, value: mock_redis_store.update({key: value})
    mock_r.get.side_effect = lambda key: mock_redis_store.get(key)
    mock_r.delete.side_effect = lambda key: mock_redis_store.pop(key, None)
    mock_r.expire.side_effect = lambda key, ttl: None
    with patch("utils.redis.r", mock_r):
        yield

# ✅ 1. 注册用户
def test_register_user():
    response = client.post("/register", json={
        "username": "testimg2img",
        "password": "testpass456@",
        "role": "user"
    })
    assert response.status_code in (200, 409)
    print("✅ Register:", response.json())
    print("❌ Register failed:", response.text)

# ✅ 2. 登录并存入 Redis
def test_login_user():
    global token, user_id
    response = client.post("/login", json={
        "username": "testimg2img",
        "password": "testpass456@"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["token"]
    user_id = data["user"]["id"]
    mock_redis_store[f"session:{token}"] = user_id
    print("✅ Token:", token)

# ✅ 3. 创建角色（结构化描述）
def test_create_character():
    global token, character_id
    headers = {"token": token}
    character_name = "KnightImg2Img"
    response = client.post("/create-character", json={
        "name": character_name,
        "description": [
            {"Name": character_name},
            {"Gender": "Male"},
            {"Personality": "Loyal and brave"},
            {"Appearance": "Steel armor and glowing sword"}
        ]
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()
    character_id = data["id"]
    assert data["name"] == character_name
    print("✅ Character created:", data)

# ✅ 4. 测试 /generate/img2img 接口
def test_generate_img2img():
    global token, character_id
    headers = {"token": token}
    db = SessionLocal()

    character_name = "KnightImg2Img"
    character = db.query(Character).filter_by(name=character_name).first()
    assert character is not None
    character_id = character.id

    # ✅ 构造描述（用于构建请求）
    description = [
        {"Name": character_name},
        {"Gender": "Male"},
        {"Personality": "Loyal and brave"},
        {"Appearance": "Steel armor and glowing sword"}
    ]

    # ✅ 本地测试图像路径（需存在）
    image_path = "/Users/dingdingdingdingding/Desktop/HKU/sem2/SmartPhone/project/final project1/final project/assets/images/yemi.jpg"  # 替换为你项目中实际的测试图像路径
    assert os.path.exists(image_path), f"❌ 图像文件不存在: {image_path}"

    with open(image_path, "rb") as img:
        response = client.post(
            "/generate/img2img",
            files={"file": ("sample.jpg", img, "image/jpeg")},
            data={
                "description": json.dumps(description),
                "character_name": character_name
            },
            headers=headers
        )

    # ✅ 响应校验
    print("🎨 Response content:", response.text)
    assert response.status_code == 200
    data = response.json()
    assert data["character_name"] == character_name
    assert data["character_id"] == character_id
    assert "image_url" in data

    # ✅ 校验 image 表插入记录
    images = db.query(Image).filter_by(character_id=character_id).all()
    assert any(img.image_type == "user_upload" and img.input_type == "img2img" for img in images), "❌ 未插入用户上传图像"
    assert any(img.image_type == "model_generated" and img.input_type == "img2img" for img in images), "❌ 未插入模型生成图像"

    # ✅ 校验 final_image_url 更新
    db.refresh(character)
    assert character.final_image_url == data["image_url"]
    print("✅ 图像生成 & 数据写入验证通过")
    db.close()