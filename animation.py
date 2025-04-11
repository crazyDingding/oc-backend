def generate_animation(inputs: str) -> str:
    """从图像和音频生成动画视频。输入为 image_path,audio_path"""
    import os
    image_path, audio_path = inputs.split(',')
    output_path = "assets/video/output.mp4"
    cmd = f"python SadTalker/inference.py --driven_audio {audio_path} --source_image {image_path} --result_dir assets/video"
    os.system(cmd)
    return output_path