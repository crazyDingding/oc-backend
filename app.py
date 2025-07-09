from flask import Flask, request, jsonify
from modules.imager.image_generator import ImageGenerator
from modules.voicer.voice_generator import VoiceGenerator
import time

app = Flask(__name__)

@app.route("/generate-avatar", methods=["POST"])
def generate_avatar():
    start_time = time.time()

    data = request.json
    description = data.get("description", [])
    dialogues = data.get("dialogues", [])

    if not description or not dialogues:
        return jsonify({"error": "Missing 'description' or 'dialogues'"}), 400

    # 获取角色名
    character_name = next((d.get("Name") for d in description if "Name" in d), "default")

    # Step 1️⃣：生成图像
    image_gen = ImageGenerator(mode="text2img")
    image_path = image_gen.generate_image(description, character_name=character_name)

    # Step 2️⃣：生成语音
    voice_gen = VoiceGenerator()
    audio_path = voice_gen.generate_voice(description, dialogues, character_name=character_name)

    # Step 3️⃣：预留生成视频（TODO）
    video_path = "TODO"

    # 返回结果
    return jsonify({
        "image": image_path,
        "voice": audio_path,
        "video": video_path,
        "time_used_sec": round(time.time() - start_time, 2)
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)