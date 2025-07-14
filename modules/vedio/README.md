# 🎬 Videoer Module

The Videoer module is responsible for generating character videos by combining image, audio, and text using the VisionStory API. It orchestrates multi-modal content—appearance, voice, and language—into a unified talking-head animation, allowing characters to “come to life” through video.

---

## 🧠 Video Generation Pipeline

The system first generates a natural language response via a text generator (default: Kimi).

Then, it uses a text-to-image engine (default: Stable Diffusion) to generate a character avatar.

The generated image is uploaded to VisionStory as a character avatar.

Finally, the system uses the avatar and generated text to synthesize a talking video through the VisionStory /video API.

The output is a playable video link that can be streamed or embedded into web apps, games, or social platforms.


## 🎥 Demo Video Generation

Below is a demonstration of a fully automated video generated using the VisionStory.generate_video_from_prompt() pipeline:
👉 **[Click here to watch](https://github.com/crazyDingding/oc-backend/raw/main/assets/audios/jessica_20250418_210509.mp3)**  
The vedio will stream directly in your browser or download depending on your device and browser settings.

---

## 📁 File Structure

```bash
modules/
└── voicer/
├── generator.py      # Voice synthesis logic
└── README.md         # Module documentation (you are here)
```
---
