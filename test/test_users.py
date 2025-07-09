import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from sqlalchemy.testing.suite.test_reflection import users
from database.database import engine
from database.base import Base

# ✅ 关键步骤：确保所有 models 被导入，Base.metadata 才知道有哪些表
import modules.users.models
import modules.character.models
import modules.texter.models
import modules.imager.models

Base.metadata.create_all(bind=engine)
from main import app

client = TestClient(app)

# 全局变量
token = None
mock_redis_store = {}

# ✅ 替换 Redis 的 setex/get/delete 函数
@pytest.fixture(autouse=True)
def mock_redis_methods():
    mock_r = MagicMock()

    mock_r.setex.side_effect = lambda key, ttl, value: mock_redis_store.update({key: value})
    mock_r.get.side_effect = lambda key: mock_redis_store.get(key)
    mock_r.delete.side_effect = lambda key: mock_redis_store.pop(key, None)
    mock_r.expire.side_effect = lambda key, ttl: None  # 可选：模拟 refresh_session

    with patch("utils.redis.r", mock_r):
        yield

# ===== 注册用户 =====
def test_register_user():
    response = client.post("/register", json={
        "username": "testuser4",
        "password": "newpass456@",
        "role": "user"
    })
    assert response.status_code in (200, 409)
    print("Register:", response.json())

# # ===== 登录用户 =====
# def test_login_user():
#     global token
#     response = client.post("/login", json={
#         "username": "testuser2",
#         "password": "newpass456@"
#     })
#     print("Login response:", response.status_code, response.json())
#     assert response.status_code == 200
#     data = response.json()
#     token = data["token"]
#     # ✅ 手动模拟 Redis 中保存 session
#     user_id = data["user"]["id"]
#     mock_redis_store[f"session:{token}"] = user_id
#     print("Login token:", token)
#
# # ===== 访问受保护路由 =====
# def test_protected_route():
#     global token
#     response = client.get("/protected-route", headers={"token": token})
#     assert response.status_code == 200
#     print("Protected route:", response.json())
#
# # ===== 未授权访问测试 =====
# def test_protected_route_fail():
#     response = client.get("/protected-route")
#     assert response.status_code in (401, 422)
#
#     response = client.get("/protected-route", headers={"token": "invalid"})
#     assert response.status_code == 401
#
# # ===== 修改密码成功 =====
# def test_change_password_success():
#     global token
#     headers = {"token": token}
#     response = client.post("/change-password", json={
#         "username": "testuser2",
#         "old_password": "newpass456@",
#         "new_password": "testpass123!"
#     }, headers=headers)
#     assert response.status_code == 200
#     print("Password changed:", response.json())
#
# # ===== 修改密码失败 =====
# def test_change_password_fail():
#     global token
#     headers = {"token": token}
#     response = client.post("/change-password", json={
#         "username": "testuser2",
#         "old_password": "wrongpass",
#         "new_password": "failpass123!"
#     }, headers=headers)
#     assert response.status_code == 400
#     print("Password change failed:", response.json())
#
# # ===== 登出并验证 token 失效 =====
# def test_logout_and_check_token_expiry():
#     global token
#     response = client.post("/logout", headers={"token": token})
#     assert response.status_code == 200
#     print("Logout:", response.json())
#
#     # 再访问应失败
#     response = client.get("/protected-route", headers={"token": token})
#     assert response.status_code == 401
#     print("Post logout access:", response.json())