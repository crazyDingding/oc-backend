# AI OC Companion System

An interactive, high-fidelity, AI-driven companion system for user-created Original Characters (OCs), integrating state-of-the-art generative models for image creation, dialogue, voice synthesis, and facial animation.

> This project is under active development by a student team from HKU.

---

## Features

- **Image & Style Generation** – High-resolution OC generation with Stable Diffusion & ControlNet
- **Text Generation** – Character-specific, context-aware dialogue via GPT-4
- **Voice Synthesis** – Expressive speech with Bark and emotional control via ElevenLabs
- **Facial Animation** – Realistic lip-sync and expressions with SadTalker + EchoMimic
- **Integrated Pipeline** – End-to-end system enabling dynamic interactions with user-defined OCs

---

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
