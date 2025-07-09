import json
import pytest
import time
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
        "username": "testuser_img",
        "password": "testpass456@",
        "role": "user"
    })
    assert response.status_code in (200, 409)
    print("✅ Register:", response.json())

# ✅ 2. 登录并存入 Redis
def test_login_user():
    global token, user_id
    response = client.post("/login", json={
        "username": "testuser_img",
        "password": "testpass456@"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["token"]
    user_id = data["user"]["id"]
    mock_redis_store[f"session:{token}"] = user_id
    print("✅ Token:", token)

# ✅ 3. 创建角色（兼容结构化描述）
def test_create_character():
    global token, character_id
    headers = {"token": token}
    character_name = "ImageKnight"
    response = client.post("/create-character", json={
        "name": character_name,
        "description": [
            {"Name": "ImageKnight"},
            {"Gender": "Male"},
            {"Personality": "Fearless"},
            {"Appearance": "Golden armor with wings"}
        ]
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()

    character_id = data["id"]
    assert data["name"] == "ImageKnight"

    print("✅ Character created:", data)

# ✅ 4. 测试图像生成接口 /generate/text2img
def test_generate_text2img():
    global token, character_id
    headers = {"token": token}

    # ✅ 构造与角色匹配的结构化描述
    request_data = {
        "description": [
            {"Name": "ImageKnight"},
            {"Gender": "Male"},
            {"Personality": "Fearless"},
            {"Appearance": "Golden armor with wings"}
        ]
    }

    response = client.post("/generate/text2img", json=request_data, headers=headers)
    print("🎨 Response content:", response.text)
    assert response.status_code == 200
    data = response.json()

    # ✅ 响应校验
    assert "image_url" in data
    assert data["character_name"] == "ImageKnight"

    db = SessionLocal()

    # ✅ 用 character_id 精准查找角色
    character = db.query(Character).filter_by(id=character_id).first()
    assert character is not None

    # ✅ 检查 final_image_url 字段更新
    db.refresh(character)
    assert character.final_image_url == data["image_url"]

    # ✅ 检查 image 表是否插入记录
    images = db.query(Image).filter_by(character_id=character.id).all()
    assert any(img.image_url == data["image_url"] for img in images)

    print("✅ 图像生成 & 数据写入验证通过")
    db.close()