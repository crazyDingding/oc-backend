🎬 Videoer Module
The Videoer module is responsible for generating character videos by combining image, audio, and text using the VisionStory API. It orchestrates multi-modal content—appearance, voice, and language—into a unified talking-head animation, allowing characters to “come to life” through video.

🧠 Video Generation Pipeline
Given a structured character description and dialogue history:

The system first generates a natural language response via a text generator (default: Kimi).

Then, it uses a text-to-image engine (default: Stable Diffusion) to generate a character avatar.

The generated image is uploaded to VisionStory as a character avatar.

Finally, the system uses the avatar and generated text to synthesize a talking video through the VisionStory /video API.

The output is a playable video link that can be streamed or embedded into web apps, games, or social platforms.

🎥 Demo Video Generation
Below is a demonstration of a fully automated video generated using the VisionStory.generate_video_from_prompt() pipeline:

👉 Click here to watch


The result showcases a female character ("Airi") speaking based on a one-line dialogue input.

⚙️ Features
🔄 End-to-end automation: From text to avatar to video.

🧩 Modular design: Replaceable text generator and image engine.

🎭 Character-aware: Avatar and voice linked to structured description (Name, Personality, Appearance).

🕘 Real-time polling: The system automatically waits for video rendering to complete.

🎨 Configurable: Customize voice_id, model_id, aspect_ratio, and resolution.

