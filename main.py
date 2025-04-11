from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.memory import VectorStoreRetrieverMemory
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from tools.image_generator import generate_image
from tools.voice_generator import generate_voice
from tools.animator import generate_animation
from memory.memory_store import create_or_load_memory

# 初始化工具
image_tool = Tool(
    name="StableDiffusion",
    func=generate_image,
    description="Generate an OC image from prompt."
)

voice_tool = Tool(
    name="BarkTTS",
    func=generate_voice,
    description="Convert text into expressive speech audio."
)

animation_tool = Tool(
    name="SadTalker",
    func=generate_animation,
    description="Generate talking face animation from image and audio."
)

# 向量记忆
embedding = OpenAIEmbeddings()  # 可替换为本地 embedding 模型
memory = create_or_load_memory("luna_memory", embedding)

# 初始化代理
llm = ChatOpenAI(temperature=0.7)
agent = initialize_agent(
    tools=[image_tool, voice_tool, animation_tool],
    llm=llm,
    memory=memory,
    agent_type="conversational-react-description",
    verbose=True
)

if __name__ == "__main__":
    print("🎀 欢迎与 Luna 对话：")
    while True:
        user_input = input("你：")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = agent.run(user_input)
        print("Luna：", response)