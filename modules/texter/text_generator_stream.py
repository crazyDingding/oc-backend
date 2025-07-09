import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator

from modules.base_module import BaseModule
from tools.prompts.text_prompt import text_prompt
from utils.llms import Kimi
from utils.utils import send_chat_prompts, extract_value_from_prompt

# 加载 .env 配置
load_dotenv(override=True)
MODEL_NAME = os.getenv('DeepSeek')
print(os.getenv('MODEL_NAME'))

# 默认的角色描述，当前端传空/“0”时使用
DEFAULT_DESCRIPTION = [
    {"Name": "Airi"},
    {"Gender": "Female"},
    {"Personality": "gentle, shy, lovely"},
    {"Appearance": "long silver hair, blue eyes, elegant dress"}
]

# 创建 FastAPI 应用
app = FastAPI(title="TextGenerator API")

# 请求体数据模型
class GenerateTextRequest(BaseModel):
    dialogues: List[Dict[str, str]]
    description: List[Dict[str, str]]

class TextGenerator(BaseModule):
    def __init__(self, llm=Kimi()):
        super().__init__(llm=llm)
        self.history: List[dict] = []
        self.character_name: Optional[str] = None

    async def generate_text_stream(self, dialogues, description) -> AsyncGenerator[str, None]:
        if not description or description == "0":
            description = DEFAULT_DESCRIPTION

        if self.character_name is None:
            self.character_name = extract_value_from_prompt(description, "Name")

        desc_text = self.transfer_data_to_prompt(description)
        system_content = (
            text_prompt["SYSTEM_PROMPT"].strip()
            + "\n\n**Persona**:\n" + desc_text
        )

        user_input = "\n".join(d["Input"].strip() for d in dialogues if d.get("Input"))

        msgs: List[dict] = [
            {"role": "system", "content": system_content}
        ]
        if len(self.history) > 10:
            self.history = self.history[-10:]
        msgs.extend(self.history)

        msgs.append({"role": "user", "content": user_input})
        msgs.append({
            "partial": True,
            "role": "assistant",
            "name": self.character_name,
            "content": ""
        })

        async for token in self.llm.chat_stream_async(msgs, temperature=0.3):
            yield token

        self.history.append({"role": "user", "content": user_input})
        # NOTE: 因为是流式返回，无法直接缓存完整 assistant 内容，可自行在前端拼接后补充

# 创建路由：POST /generate-text-stream
@app.post("/generate-text-stream")
async def generate_text_stream_api(request: GenerateTextRequest):
    generator = TextGenerator()
    async def token_stream():
        async for token in generator.generate_text_stream(request.dialogues, request.description):
            yield token
    return StreamingResponse(token_stream(), media_type="text/plain")

# 测试入口（仅调试用）
if __name__ == '__main__':
    dialogues = [{"Input": "How are you today?"}]
    description = "0"

    text_generator = TextGenerator()

    async def run():
        async for token in text_generator.generate_text_stream(dialogues, description):
            print(token, end="")

    asyncio.run(run())
