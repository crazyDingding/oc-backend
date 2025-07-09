import json

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from database.database import SessionLocal
from main import app
from modules.character.models import Character
from modules.texter import Dialogue
import modules.users.models
import modules.character.models
import modules.texter.models
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

# 1. 注册用户（注意使用 data 不是 json）
def test_register_user():
    response = client.post("/register", json={
        "username": "testuser31",
        "password": "testpass456@",
        "role": "user"
    })
    assert response.status_code in (200, 409)
    print("✅ Register:", response.json())

# 2. 登录并存入 Redis
def test_login_user():
    global token, user_id
    response = client.post("/login", json={
        "username": "testuser31",
        "password": "testpass456@"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["token"]
    user_id = data["user"]["id"]
    mock_redis_store[f"session:{token}"] = user_id
    print("✅ Token:", token)

# 3. 创建角色（兼容新版结构化描述）
def test_create_character():
    global token, character_id
    headers = {"token": token}
    response = client.post("/create-character", json={
        "name": "AI Knight1",
        "description": [
            {"Name": "AI Knight"},
            {"Gender": "Male"},
            {"Personality": "Brave"},
            {"Appearance": "Silver armor and blue cape"}
        ]
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()

    character_id = data["id"]
    assert data["name"] == "AI Knight"

    # ✅ 确保 description 为 JSON 可解析格式
    parsed_description = json.loads(data["description"])
    assert isinstance(parsed_description, list)
    assert any("Name" in item for item in parsed_description)

    print("✅ Character created with structured description:", parsed_description)

# ✅ 4. 测试文本生成接口 /generate-text（更新后的接口格式）
def test_generate_text():
    global token, character_id
    headers = {"token": token}

    request_data = {
        "dialogues": [
            {"Input": "I'm so sad."}
        ],
        "description": [
            {"Name": "AI Knight"},
            {"Gender": "Male"},
            {"Personality": "Brave"},
            {"Appearance": "Silver armor and blue cape"}
        ]
    }

    response = client.post("/generate-text", json=request_data, headers=headers)
    print("🔥 Response content:", response.text)
    assert response.status_code == 200
    data = response.json()

    assert "result" in data
    assert "SampleSpeech" in data["result"]
    generated_text = data["result"]["SampleSpeech"]

    db = SessionLocal()

    # ✅ 用 character_id 精准查角色
    character = db.query(Character).filter_by(id=character_id).first()
    assert character is not None

    db.refresh(character)  # 确保刷新字段
    assert character.generated_dialogue == generated_text

    # ✅ 检查对话写入
    dialogues = db.query(Dialogue).filter_by(character_id=character.id).all()
    assert any(d.content == "I'm so sad." for d in dialogues)
    assert any(d.content == generated_text for d in dialogues)

    print("✅ 文本生成 & 数据写入验证通过")