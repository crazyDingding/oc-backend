import json
import os
import sys
from datetime import datetime
from uuid import uuid4
from typing import Optional, List, Dict

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from modules.imager.image_generator import ImageGenerator
from modules.imager import crud as image_crud, schemas as image_schemas
from modules.imager.schemas import ImageCreate
from modules.texter.schemas import DialogueCreate
from modules.texter.text_generator import TextGenerator
from modules.users.models import User
from modules.character import schemas as character_schemas
from modules.character import crud as character_crud
from tools.character.manager import CharacterPromptManager
from utils.redis import delete_session

# 添加路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from database.database import SessionLocal, engine
from utils.llms import Kimi, StableDiffusion
from utils.utils import extract_value_from_description, upload_to_imgbb, convert_image_to_png
from utils.redis import get_session, r, get_user_id_by_token
from utils.security import verify_password, hash_password
from tools.prompts.text_prompt import text_prompt
from modules.base_module import BaseModule
from modules.users import models, schemas, crud
from modules.users.schemas import ChangePasswordRequest
from modules.users.dependencies import get_db, get_current_user
from modules.texter import crud as dialogue_crud

# 初始化 FastAPI 应用
app = FastAPI(title="Unified AI API Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# 创建数据库表
models.Base.metadata.create_all(bind=engine)


# ======================= 获取描述接口 =======================
@app.post("/create-character")
def create_character_api(
    character: character_schemas.CharacterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    description = character.description

    # ✅ Step 1: 判空或无效输入（空字符串、"0"、空列表等）
    if (
        description in (None, "", "0") or
        (isinstance(description, list) and all(
            not any(v.strip() for v in item.values() if isinstance(v, str))
            for item in description
        ))
    ):
        manager = CharacterPromptManager(user_id=current_user.id, redis_client=r)
        description = manager.get_rotating_default_description()

    # ✅ Step 2: 统一转字符串入库
    if isinstance(description, list):
        description = json.dumps(description, ensure_ascii=False)

    # ✅ Step 3: 清理原始字段，避免 pydantic 校验失败
    character_data = character.dict()
    character_data["description"] = description  # 已转为 str
    updated_character = character_schemas.CharacterCreate(**character_data)

    # ✅ Step 4: 创建角色
    return character_crud.create_character(
        db=db,
        character=updated_character,
        user_id=current_user.id,
        description=description
    )

@app.get("/my-characters")
def get_my_characters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    characters = character_crud.get_characters_by_user(db, current_user.id)
    return characters

def save_temp_file(file: UploadFile) -> str:
    upload_dir = os.path.join(os.getcwd(), "temp_uploads")
    os.makedirs(upload_dir, exist_ok=True)  # 自动创建目录
    file_ext = os.path.splitext(file.filename)[-1] or ".png"
    file_path = os.path.join(upload_dir, f"user_upload_{uuid4().hex}{file_ext}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path

@app.post("/upload-character-image")
async def upload_character_image(
    character_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Step 1: 保存临时文件
    file_path = save_temp_file(file)

    # Step 2: 上传到 imgbb
    public_url = upload_to_imgbb(file_path)
    if not public_url:
        raise HTTPException(500, detail="Upload to hosting failed")

    # Step 3: 更新数据库字段 final_image_url
    character_crud.update_character_final_image_url(db, character_id, public_url)

    return {"character_id": character_id, "final_image_url": public_url}

# ======================= 图像生成接口 =======================
class Text2ImgRequest(BaseModel):
    description: List[Dict[str, str]]


@app.post("/generate/text2img")
def generate_text2img(
    request: Text2ImgRequest,
    db: Session = Depends(get_db)
):
    # ✅ Step 1: 提取角色名
    character_name = extract_value_from_description(request.description, key="Name")
    if character_name == "unknown":
        raise HTTPException(status_code=400, detail="Character name not found in description")

    # ✅ Step 2: 查询角色信息
    character = character_crud.get_character_by_name(db, character_name)
    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_name}' not found")

    character_id = character.id

    # ✅ Step 3: 使用数据库中的完整角色描述（结构化 or 纯文本包装）
    print("🔥 当前角色名：", character.name)
    print("🔥 数据库中 description 类型：", type(character.description))
    print("🔥 数据库中 description 内容：", character.description)

    if isinstance(character.description, str):
        try:
            parsed = json.loads(character.description)
            if isinstance(parsed, list):
                full_description = parsed
            else:
                full_description = [{"RawDescription": character.description}]
        except Exception:
            full_description = [{"RawDescription": character.description}]
    elif isinstance(character.description, list):
        full_description = character.description
    else:
        raise HTTPException(status_code=500, detail="Character description format is invalid")

    # ✅ Step 4: 调用图像生成器
    generator = ImageGenerator(mode="text2img")
    image_url, _ = generator.generate_image(
        description=full_description,
        character_name=character.name
    )

    if not image_url:
        raise HTTPException(status_code=500, detail="Image generation failed")

    # ✅ Step 5: 写入 Image 表
    image_data = ImageCreate(
        character_id=character_id,
        image_type="model_generated",
        input_type="text2img",
        image_url=image_url
    )
    image_crud.create_image(db, image_data)

    # ✅ Step 6: 更新角色头像字段
    character_crud.update_character_final_image_url(db, character_id, image_url)

    # ✅ Step 7: 返回响应
    return {
        "character_name": character.name,
        "image_url": image_url
    }



@app.post("/generate/img2img")
async def generate_img2img(
    description: str = Form(...),
    file: UploadFile = File(...),
    character_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):

    # ✅ Step 1: 提取角色名（优先使用 character_name 参数，其次从 description 中提取）
    try:
        description_json = json.loads(description)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid description format. Must be a JSON string list.")

    if character_name and character_name.strip():
        character_name = character_name.strip()
    else:
        character_name = extract_value_from_description(description_json, key="Name")
        if character_name == "unknown":
            raise HTTPException(status_code=400, detail="Character name not found in description")

    # ✅ Step 2: 查询角色信息
    character = character_crud.get_character_by_name(db, character_name)
    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_name}' not found")

    character_id = character.id

    # ✅ Step 3: 使用数据库中的完整描述（结构化 or 包装成 RawDescription）
    try:
        stored_description = character.description
        if isinstance(stored_description, str):
            parsed = json.loads(stored_description)
            if isinstance(parsed, list):
                full_description = parsed
            else:
                full_description = [{"RawDescription": stored_description}]
        else:
            full_description = [{"RawDescription": str(stored_description)}]
    except Exception:
        full_description = [{"RawDescription": character.description}]

    # ✅ Step 3 (替代): 保存文件 + 上传 imgbb
    file_path = save_temp_file(file)
    user_image_url = upload_to_imgbb(file_path)
    if not user_image_url:
        raise HTTPException(status_code=500, detail="Upload to image host failed")

    # ✅ Step 3 (continued): 写入 Image 表，标记为用户上传图像
    image_crud.create_image(
        db,
        ImageCreate(
            character_id=character_id,
            image_type="user_upload",
            input_type="img2img",
            image_url=user_image_url
        )
    )

    # ✅ Step 4: 调用图像生成器
    generator = ImageGenerator(mode="img2img")
    generated_image_url, _ = generator.generate_image(
        description=full_description,
        character_name=character.name,
        init_image_path=file_path
    )

    if not generated_image_url:
        raise HTTPException(status_code=500, detail="Image generation failed")

    # ✅ Step 5: 写入模型生成图像记录
    image_crud.create_image(
        db,
        ImageCreate(
            character_id=character_id,
            image_type="model_generated",
            input_type="img2img",
            image_url=generated_image_url
        )
    )

    # ✅ Step 6: 更新角色头像字段
    character_crud.update_character_final_image_url(db, character_id, generated_image_url)

    # ✅ Step 7: 返回响应
    return {
        "character_name": character.name,
        "character_id": character_id,
        "image_url": generated_image_url
    }

# ======================= 文本生成接口 =======================
class DialogueItem(BaseModel):
    sender: str  # "user" or "character"
    content: str

class GenerateTextRequest(BaseModel):
    dialogues: List[Dict[str, str]]
    description: List[Dict[str, str]]

router = APIRouter()
@router.post("/generate-text")
async def generate_text_api(
    request: GenerateTextRequest,
    db: Session = Depends(get_db)
):
    # 1. 提取角色名（从请求体的 description 中提取 Name 字段）
    character_name = extract_value_from_description(request.description, key="Name")
    if character_name == "unknown":
        raise HTTPException(status_code=400, detail="Character name not found in description")

    # 2. 查询角色信息（角色名唯一，由前端保证）
    character = character_crud.get_character_by_name(db, character_name)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # 3. 使用数据库中保存的完整角色描述
    print("🔥 当前角色名：", character.name)
    print("🔥 数据库中 description 类型：", type(character.description))
    print("🔥 数据库中 description 内容：", character.description)

    if isinstance(character.description, str):
        try:
            # 尝试解析为结构化 JSON
            parsed = json.loads(character.description)
            if isinstance(parsed, list):
                full_description = parsed
            else:
                # 如果是普通字符串而非 JSON list，则包装为单项 list 结构
                full_description = [{"RawDescription": character.description}]
        except Exception:
            # 非 JSON 字符串，说明是纯文本描述，包装处理
            full_description = [{"RawDescription": character.description}]
    elif isinstance(character.description, list):
        full_description = character.description
    else:
        raise HTTPException(status_code=500, detail="Character description format is invalid")

    # 4. 格式化对话内容
    formatted_dialogues = request.dialogues

    # 5. 入库用户对话
    for d in request.dialogues:
        content = d.get("Input") or d.get("content")
        if content and content.strip():
            dialogue = DialogueCreate(
                character_id=character.id,
                sender="user",  # 或从 d.get("sender") 取也行
                content=content.strip()
            )
            dialogue_crud.create_dialogue(db, dialogue)

    # 6. 调用文本生成器
    generator = TextGenerator()
    result = await generator.generate_text(
        dialogues=request.dialogues,  # 用原始格式也可以
        description=full_description,
        character_name=character.name
    )

    # 7. 角色回复
    reply_text = result.get("SampleSpeech", "") if isinstance(result, dict) else str(result)

    # 8. 存入角色回复
    reply = DialogueCreate(
        character_id=character.id,
        sender="character",
        content=reply_text
    )
    dialogue_crud.create_dialogue(db, reply)

    # 9. 更新 character.generated_dialogue 字段
    character.generated_dialogue = reply_text
    db.flush()  # 确保 pending changes 入库
    db.refresh(character)  # 刷新当前对象的最新值
    db.commit()

    # 10. 返回响应
    return {
        "result": result
    }

# ======================= 用户认证接口 =======================
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.register_user(db, user)

@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.login_user(db, user)


@app.get("/protected-route")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}"}

@app.post("/logout")
def logout(token: str = Header(...)):
    delete_session(token)
    return {"message": "Logged out successfully"}

@app.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.change_password(db, current_user.id, request.old_password, request.new_password)

app.include_router(router)