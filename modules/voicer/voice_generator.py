# modules/voice/voice_generator.py

import os
from modules.texter.text_generator_stream import TextGenerator
from utils.llms import ElevenLabs, DeepSeek
from utils.utils import extract_value_from_description


class VoiceGenerator:
    def __init__(self, text_llm=None, tts_engine=None):
        """
        VoiceGenerator combines text generation with voice synthesis.

        Args:
            text_llm: A language model (e.g., DeepSeek) for generating the response
            tts_engine: A TTS engine instance (e.g., ElevenLabs)
        """
        self.text_generator = TextGenerator(llm=DeepSeek())
        self.tts = tts_engine or ElevenLabs()

    def generate_voice(self, description, dialogues, character_name=None, output_path=None):
        """
        Generates a SampleSpeech using a language model and converts it to voice.

        Args:
            description (list[dict]): Character attributes
            dialogues (list[dict]): Example dialogue inputs
            character_name (str): Character name override (optional)
            output_path (str): Optional path to save the audio

        Returns:
            str: The path to the generated audio file
        """
        print("📥 Generating SampleSpeech from character profile and dialogues...")
        result = self.text_generator.generate_text(dialogues, description)

        sample_speech = None
        if isinstance(result, dict) and "SampleSpeech" in result:
            sample_speech = result["SampleSpeech"]
        else:
            print("⚠️ SampleSpeech not found in model output.")
            return None

        # 自动提取角色名（如果未提供）
        if not character_name:
            character_name = extract_value_from_description(description, key="Name")
            print("📌 提取角色名为：", character_name)

        print(f"🗣️ Generating voice for {character_name} using ElevenLabs...")
        audio_path = self.tts.synthesize(
            text=sample_speech,
            character_name=character_name,
            output_path=output_path
        )
        print("✅ 音频文件保存位置：", audio_path)
        return audio_path

if __name__ == '__main__':
    dialogues = [{"Input": "I'm so sad."}]
    description = [
        {"Name": "Jessica"},
        {"Gender": "Female"},
        {"Personality": "Gentle"}
    ]
    voice_generator = VoiceGenerator()
    result = voice_generator.generate_voice(description, dialogues)

    print("✅ 模型输出：")
