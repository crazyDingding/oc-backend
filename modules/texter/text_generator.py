import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

from modules.base_module import BaseModule
from tools.prompts.text_prompt import text_prompt
from utils.llms import Kimi
from utils.utils import send_chat_prompts, extract_value_from_prompt

# 加载 .env 配置
load_dotenv(override=True)
MODEL_NAME = os.getenv('DeepSeek')
print(os.getenv('MODEL_NAME'))


# 创建 FastAPI 应用
app = FastAPI(title="TextGenerator API")

# 请求体数据模型
class GenerateTextRequest(BaseModel):
    dialogues: List[Dict[str, str]]
    description: List[Dict[str, str]]

class TextGenerator(BaseModule):
    def __init__(self, llm=Kimi()):
        super().__init__(llm=llm)
        self.history: List[dict] = []            # 存纯 role+content
        self.character_name: Optional[str] = None

    async def generate_text(self, dialogues, description, character_name: Optional[str] = None):
        # —— 1. 获取有效角色描述（支持轮换）
        print("🧪 使用角色描述：", description)

        # —— 2. 抽角色名
        if self.character_name is None and character_name:
            self.character_name = character_name

        # —— 3. 构建 system prompt
        desc_text = self.transfer_data_to_prompt(description)
        system_content = (
            text_prompt["SYSTEM_PROMPT"].strip()
            + "\n\n**Persona**:\n" + desc_text
        )

        # —— 4. 合并所有 dialogues 为一句 user_input（也可按条塞，视你需求）
        user_input = "\n".join(d["Input"].strip() for d in dialogues if d.get("Input"))

        # —— 5. 开始构建本次请求的 messages 列表
        msgs: List[dict] = [
            {"role": "system", "content": system_content}
        ]
        # 限制历史长度，假设保留最新 10 条
        #TODO：用redis来保存记录
        if len(self.history) > 10:
            self.history = self.history[-10:]
        msgs.extend(self.history)

        # 加入本轮用户
        msgs.append({"role": "user", "content": user_input})

        # **只有最后一条**带 partial/name，符合 Moonshot Partial Mode
        msgs.append({
            "partial": True,
            "role": "assistant",
            "name": self.character_name,
            "content": ""
        })

        # —— 6. 发送给 Kimi
        response = await self.llm.chat(msgs, temperature=0.3, prefix="Overall")

        # —— 7. 更新纯净历史
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        # —— 8. 返回最终回答
        return self.extract_content_from_response(response)

# 创建路由：POST /generate-text
@app.post("/generate-text")
async def generate_text_api(request: GenerateTextRequest):
    generator = TextGenerator()
    result = await generator.generate_text(request.dialogues, request.description)
    return {"result": result}

# 测试入口（仅调试用）
if __name__ == '__main__':
    import asyncio
    from tools.character.manager import CharacterPromptManager
    from utils.redis import r  # 你之前定义好的 redis 实例

    # 模拟请求输入
    user_id = 87  # 你可以根据测试需要换成其他数字
    dialogues = [{"Input": "How are you today?"}]
    description_raw = "0"  # 非法描述，触发默认轮换角色

    # 创建默认角色管理器，并生成角色描述
    manager = CharacterPromptManager(user_id=user_id, redis_client=r)
    description = manager.get_character_description(description_raw)
    character_name = manager._extract_name(description)

    # 实例化文本生成器并生成文本
    text_generator = TextGenerator()
    result = asyncio.run(text_generator.generate_text(dialogues, description, character_name=character_name))

    # 打印输出
    print(dialogues)
    print("✅ 模型输出：")
    print(result)
