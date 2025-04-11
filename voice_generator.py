def generate_voice(text: str) -> str:
    """文本转语音，返回音频文件路径"""
    import torchaudio
    from bark import generate_audio, preload_models, save_as_prompt
    preload_models()
    audio_array = generate_audio(text)
    filename = "assets/audio/output.wav"
    torchaudio.save(filename, audio_array, 24000)
    return filename