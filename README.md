# OC-Backend
# AI OC Companion System

**OC-Backend** is the backend system for an AI-powered companion platform that brings user-designed Original Characters (OCs) to life. It supports text generation, image synthesis (text-to-image and image-to-image), multilingual voice generation, and character interaction—all powered by advanced language and multimodal models like GPT-4 Turbo, DeepSeek Reasoner, Stable Diffusion, Moonshot Kimi, and ElevenLabs.
An interactive, high-fidelity, AI-driven companion system for user-created Original Characters (OCs), integrating state-of-the-art generative models for image creation, dialogue, voice synthesis, and facial animation.

---

## 🧩 Features

- 🔮 **Multimodal AI Interaction**: Text, image, and voice responses
- ⚙️ **Multiple LLM Providers**: OpenAI, DeepSeek, Kimi, LLaMA (optional local)
- 🖼️ **Image generation**: Text-to-Image & Image-to-Image using Stable Diffusion API
- 🗣️ **Voice synthesis**: Multilingual TTS with ElevenLabs
- 🧠 **Character memory & dialogue management**
- 🛠️ **Modular environment for local or cloud deployment**
> This project is under active development by a student team from HKU.

---

## ⚙️ 1. Clone the Repository

```bash
git clone https://github.com/crazyDingding/oc-backend.git
cd oc-backend
```
## 🔐 2. Create a .env File

Create a `.env` file in the root directory with the following structure (replace values with your actual API keys):
## Features

```env
# Model Settings
MODEL_NAME="gpt-4-turbo"
DS_MODEL_NAME="deepseek-reasoner"
KIMI_MODEL_NAME="moonshot-v1-8k"
SD_MODEL_NAME="flux"
VOICE_MODEL_NAME="eleven_multilingual_v2"
MODEL_TYPE="OpenAI"

# API Keys
DS_API_KEY=your_deepseek_api_key
KIMI_API_KEY=your_kimi_api_key
VOICE_API_KEY=your_elevenlabs_api_key
SD_API_KEY=your_stablediffusion_api_key
UPLOAD_API_KEY=your_upload_key
OPENAI_API_KEY=your_openai_api_key
MINIMAX=your_minimax_token

# Voice Settings
VOICE_ID=your_elevenlabs_voice_id
ELEVENLABS_OUTPUT_FORMAT="mp3_44100_128"

# Database
DATABASE=your_postgresql_url
DATABASEIPV4=your_ipv4_postgresql_url

# Proxy (Optional for VPN users)
API_BASE_URL="http://127.0.0.1:7890"
HTTP_PROXY="http://127.0.0.1:7890"
HTTPS_PROXY="http://127.0.0.1:7890"
ALL_PROXY="socks5://127.0.0.1:7890"
```
Do not commit this file to GitHub. Add .env to your .gitignore.
- **Image & Style Generation** – High-resolution OC generation with Stable Diffusion & ControlNet
- **Text Generation** – Character-specific, context-aware dialogue via GPT-4
- **Voice Synthesis** – Expressive speech with Bark and emotional control via ElevenLabs
- **Facial Animation** – Realistic lip-sync and expressions with SadTalker + EchoMimic
- **Integrated Pipeline** – End-to-end system enabling dynamic interactions with user-defined OCs

---
## 📦 3. Install Dependencies

Activate your Python virtual environment (optional):

```bash
conda activate oc-backend  # or use venv
```
Install Python dependencies:
```bash
pip install -r requirements.txt
```
---
## 🚀 4. Run the FastAPI Server

Start the backend server using Uvicorn:

```bash
uvicorn app:app --reload --port 8000
```
Access the API at:
```bash
http://localhost:8000
```

---

## 🧠 🐏 5. (Optional) Run LLaMA Locally with Ollama

To run LLaMA 3 locally instead of using OpenAI:

### Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Run the LLaMA model
```bash
ollama run llama3
```
Add the following to your .env
```bash
MODEL_NAME="llama3"
MODEL_TYPE="OLLAMA"
EMBED_MODEL_TYPE="OLLAMA"
EMBED_MODEL_NAME="nomic-embed-text"
MODEL_SERVER="http://localhost:11434"
```
Also export:
```bash
export NO_PROXY=localhost,127.0.0.1
```
---


## 📡 Example API Endpoints

### ✅ Health Check

```http
GET /ping
```
🎭 Character-Based Chat
```bash
POST /chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Hi!"},
    {"role": "assistant", "content": "Hello there!"}
  ],
  "character_name": "Airi"
}
```
🖼️ Text-to-Image Generation
```bash
POST /generate/text2img
Form Data:
- description: (JSON string of character appearance)
- character_name: optional
```
Example
```bash
{
  "Name": "Airi",
  "Appearance": "Pink hair, cyberpunk outfit, holding a holographic tablet"
}
```
🖼️ Image-to-Image Generation
```bash
POST /generate/img2img
Form Data:
- file: Image to transform
- description: JSON string with modifications
- character_name: optional
```
📦 Character Info Retrieval
```bash
GET /character/{character_name}
```

---

## 📄 License

This project is under development for academic and research use only. Not intended for commercial distribution or production deployment.

## 🤝 Acknowledgments

- [OpenAI](https://openai.com)
- [DeepSeek](https://deepseek.com)
- [Moonshot AI](https://platform.moonshot.cn/)
- [ElevenLabs](https://elevenlabs.io)
- [Stability AI](https://stablediffusionweb.com/)
- [Supabase](https://supabase.com)
- [Ollama](https://ollama.com)
## Project Structure

```bash
ai-oc-backend/
├── backend/
│   ├── text_agent/           # GPT-4 dialogue logic
│   ├── voice_agent/          # Bark & ElevenLabs TTS modules
│   ├── animation_agent/      # SadTalker & EchoMimic integration
│   ├── image_agent/          # Stable Diffusion + ControlNet generation
│   └── orchestrator/         # Controls full-generation flow
├── data/
│   ├── oc_samples/           # Input sketches / prompts
│   └── processed/            # Intermediate or generated data
├── scripts/
│   ├── inference_pipeline.py # One-click generation pipeline
│   └── setup_env.sh          # Environment setup script
├── requirements.txt
└── .gitignore
