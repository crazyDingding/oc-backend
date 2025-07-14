# 🧠 Texter Module

The **Texter** module powers the text generation capabilities of the AI-powered companion system. It supports multiple large language models and provides both regular and streaming output for real-time interactions.

## 🚀 Features

- Supports OpenAI GPT, Moonshot Kimi, DeepSeek Reasoner, and other APIs.
- Enables **partial (streaming)** response output.
- Integrates character persona conditioning.
- Built with FastAPI, easily extendable.

## 🎞️ Streaming Output Demo

Below is a demonstration of the **streaming text generation** capability of the Texter module:

![Streaming Output Demo](https://github.com/crazyDingding/oc-backend/raw/main/assets/texts/output.gif)

> The gif shows how the model responds token by token in real-time.

## 📁 File Structure
```bash
modules/
└── texter/
├── init.py           # Module init
├── generator.py          # Text generation logic
├── router.py             # FastAPI routes
└── README.md             # Module documentation (you are here)
```
## 📡 Example API Call

You can test the endpoint using `curl`:

```bash
curl -X 'POST' \
  'http://joypal.natapp1.cc/generate-text' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "dialogues": [
    {"Input": "I'\''m so sad."}
  ],
  "description": [
    {"Name": "tom"},
    {"Gender": "Female"},
    {"Personality": "Gentle"},
    {"Appearance": "long silver hair, blue eyes, elegant dress"}
  ]
}'
```
## 🔄 Expected Output
The API will respond with a character-generated reply, optionally streamed if partial mode is enabled.
