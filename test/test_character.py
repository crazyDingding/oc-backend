import json

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
import modules.users.models
import modules.character.models
import modules.texter.models
import modules.imager.models

client = TestClient(app)
SAMPLE_JPG = "/Users/dingdingdingdingding/Desktop/HKU/sem2/SmartPhone/project/final project1/final project/assets/images/sample_input.jpg"

# 全局变量
token = None
user_id = None
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

# 1. 注册用户
def test_register_user():
    response = client.post("/register", json={
        "username": "testuser23",
        "password": "testpass456@",
        "role": "user"
    })
    assert response.status_code in (200, 409)
    print("✅ Register:", response.json())

# 2. 登录获取 token 并写入 mock Redis
def test_login_user():
    global token, user_id
    response = client.post("/login", json={
        "username": "testuser23",
        "password": "testpass456@"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["token"]
    user_id = data["user"]["id"]
    # ✅ 手动写入 session:token -> user_id
    mock_redis_store[f"session:{token}"] = user_id
    print("✅ Token:", token)

# 3. 创建角色 - 测试 description 合法情况
def test_create_character_with_custom_description():
    global token
    headers = {"token": token}
    response = client.post("/create-character", json={
        "name": "Test Custom Hero",
        "description": [
            {"Name": "Alice"},
            {"Gender": "Female"},
            {"Personality": "Kind"},
            {"Appearance": "Short hair"}
        ]
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Custom Hero"

    # ✅ 解析 description
    parsed_description = json.loads(data["description"])
    assert isinstance(parsed_description, list)
    assert any("Name" in item for item in parsed_description)
    print("✅ Custom Character created:", parsed_description)

# 3.1 创建角色 - 测试 description 为空，使用默认轮换池
def test_create_character_with_empty_description():
    global token
    headers = {"token": token}
    response = client.post("/create-character", json={
        "name": "Fallback Hero",
        "description": []  # 空 description，应触发默认轮换
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fallback Hero"

    # ✅ 解析默认 description
    parsed_description = json.loads(data["description"])
    assert isinstance(parsed_description, list)
    assert any("Name" in item for item in parsed_description)
    print("✅ Default Character created via fallback:", parsed_description)

# 4. 查询角色列表
def test_get_characters_by_user():
    global token
    headers = {"token": token}
    response = client.get("/my-characters", headers=headers)
    assert response.status_code == 200
    characters = response.json()
    assert isinstance(characters, list)
    assert any(c["name"] in ["Test Custom Hero", "Fallback Hero"] for c in characters)
    print("✅ Character list:", characters)

# 5. 上传图片更新角色头像
def test_upload_character_image():
    global token
    headers = {"token": token}

    # 获取角色列表，找出 “Test Custom Hero”
    response = client.get("/my-characters", headers=headers)
    assert response.status_code == 200
    characters = response.json()
    target = next((c for c in characters if c["name"] == "Test Custom Hero"), None)
    assert target is not None, "角色 Test Custom Hero 未找到"

    character_id = target["id"]

    # 打开本地图片并上传
    with open(SAMPLE_JPG, "rb") as f:
        files = {"file": ("sample_input.jpg", f, "image/jpeg")}
        data = {"character_id": str(character_id)}
        response = client.post("/upload-character-image", headers=headers, data=data, files=files)

    assert response.status_code == 200
    res_data = response.json()

    # ✅ 使用 final_image_url 校验
    assert "final_image_url" in res_data
    assert res_data["final_image_url"].startswith("http"), "返回 URL 非公网地址"

    print("✅ 上传图片成功，URL:", res_data["final_image_url"])