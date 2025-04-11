def generate_image(prompt: str) -> str:
    """生成图像，返回文件路径"""
    from diffusers import StableDiffusionPipeline
    import torch
    pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5").to("cuda")
    image = pipe(prompt).images[0]
    filename = "assets/images/output.png"
    image.save(filename)
    return filename