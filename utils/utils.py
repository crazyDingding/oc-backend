import copy
import json
import logging
import os
import re
import string
from uuid import uuid4

import numpy as np
from PIL import Image
from dotenv import load_dotenv
import requests
from pydub import AudioSegment


def save_json(file_path, new_json_content):
    """
    Saves JSON content to a file.

    Args:
        file_path (str): The path to the JSON file.
        new_json_content (dict or list): The new JSON content to be saved.

    Returns:
        None
    """

    # Check if the file exists
    if os.path.exists(file_path):
        # If the file exists, read its content
        with open(file_path, 'r') as f:
            json_content = json.load(f)

        # Check the type of existing JSON content
        if isinstance(json_content, list):
            # If the existing content is a list, append or extend the new content
            if isinstance(new_json_content, list):
                json_content.extend(new_json_content)
            else:
                json_content.append(new_json_content)
        elif isinstance(json_content, dict):
            # If the existing content is a dictionary, update it with the new content
            if isinstance(new_json_content, dict):
                json_content.update(new_json_content)
            else:
                # If the new content is not a dictionary, return without saving
                return
        else:
            # If the existing content is neither a list nor a dictionary, return without saving
            return

        # Write the updated JSON content back to the file
        with open(file_path, 'w') as f:
            json.dump(json_content, f, indent=4)
    else:
        # If the file does not exist, create a new file and write the new content to it
        with open(file_path, 'w') as f:
            json.dump(new_json_content, f, indent=4)


def read_json(file_path):
    """
    Reads JSON content from a file.

    Args:
        file_path (str): The path to the JSON file to be read.

    Returns:
        dict or list: The JSON content read from the file. If the file contains a JSON object, it returns a dictionary.
                      If the file contains a JSON array, it returns a list.
    """
    with open(file_path, 'r') as f:
        json_content = json.load(f)
    return json_content

def clean_string(text):
    """
    Cleans a given string by performing various operations such as whitespace normalization,
    removal of backslashes, and replacement of hash characters with spaces. It also reduces
    consecutive non-alphanumeric characters to a single occurrence.

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text after applying all the specified cleaning operations.
    """
    # Replacement of newline characters:
    text = text.replace("\n", " ")

    # Stripping and reducing multiple spaces to single:
    cleaned_text = re.sub(r"\s+", " ", text.strip())

    # Removing backslashes:
    cleaned_text = cleaned_text.replace("\\", "")

    # Replacing hash characters:
    cleaned_text = cleaned_text.replace("#", " ")

    # Eliminating consecutive non-alphanumeric characters:
    # This regex identifies consecutive non-alphanumeric characters (i.e., not
    # a word character [a-zA-Z0-9_] and not a whitespace) in the string
    # and replaces each group of such characters with a single occurrence of
    # that character.
    # For example, "!!! hello !!!" would become "! hello !".
    cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)

    return cleaned_text


def is_readable(s):
    """
    Heuristic to determine if a string is "readable" (mostly contains printable characters and forms meaningful words)

    :param s: string
    :return: True if the string is more than 95% printable.
    """
    try:
        printable_ratio = sum(c in string.printable for c in s) / len(s)
    except ZeroDivisionError:
        logging.warning("Empty string processed as unreadable")
        printable_ratio = 0
    return printable_ratio > 0.95  # 95% of characters are printable


def is_valid_json_string(source: str):
    """
    Checks if a given string is a valid JSON.

    Args:
        source (str): The string to be validated as JSON.

    Returns:
        bool: True if the given string is a valid JSON format, False otherwise.
    """
    try:
        _ = json.loads(source)
        return True
    except json.JSONDecodeError:
        logging.error(
            "Insert valid string format of JSON. \
            Check the docs to see the supported formats - `https://docs.embedchain.ai/data-sources/json`"
        )
        return False

def generate_prompt(template: str, replace_dict: dict):
    """
    Generates a string by replacing placeholders in a template with values from a dictionary.

    Args:
        template (str): The template string containing placeholders to be replaced.
        replace_dict (dict): A dictionary where each key corresponds to a placeholder in the template
                             and each value is the replacement for that placeholder.

    Returns:
        str: The resulting string after all placeholders have been replaced with their corresponding values.
    """
    prompt = copy.deepcopy(template)
    for k, v in replace_dict.items():
        prompt = prompt.replace(k, str(v))
    return prompt

def extract_value_from_description(description, key="Name"):
    """
    Extract a value from a list of single-key dictionaries.

    Args:
        description (list[dict]): The character description
        key (str): The key to look for (default: 'Name')

    Returns:
        str: The value associated with the key, or 'unknown'
    """
    print("[Debug] 原始 description：", description)
    for item in description:
        if key in item:
            return item[key]
    return "unknown"

def send_chat_prompts(sys_prompt, user_prompt, llm, prefix=""):
    """
    Sends a sequence of chat prompts to a language learning model (LLM) and returns the model's response.

    Args:
        sys_prompt (str): The system prompt that sets the context or provides instructions for the language learning model.
        user_prompt (str): The user prompt that contains the specific query or command intended for the language learning model.
        llm (object): The language learning model to which the prompts are sent. This model is expected to have a `chat` method that accepts structured prompts.

    Returns:
        The response from the language learning model, which is typically a string containing the model's answer or generated content based on the provided prompts.

    The function is a utility for simplifying the process of sending structured chat prompts to a language learning model and parsing its response, useful in scenarios where dynamic interaction with the model is required.
    """
    message = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ]
    return llm.chat(message, prefix=prefix)

def parse_description_from_input(user_input: str) -> list:
    """
    Parse a character description from user input text.

    Args:
        user_input (str): A string input by user, e.g. "Her name is Jessica. She's a gentle female character."

    Returns:
        list[dict]: A description list like [{"Name": "Jessica"}, {"Gender": "Female"}, {"Personality": "Gentle"}]
    """

    description = []

    # 提取名字（Her name is Jessica 或 My name is...）
    name_match = re.search(r"(?:her|his|my)?\s*name\s*is\s*([A-Z][a-z]+)", user_input, re.IGNORECASE)
    if name_match:
        description.append({"Name": name_match.group(1)})

    # 提取性别
    gender_match = re.search(r"\b(she|her|female|girl|woman|he|his|male|boy|man)\b", user_input, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).lower()
        gender = "Female" if gender in {"she", "her", "female", "girl", "woman"} else "Male"
        description.append({"Gender": gender})

    # 提取性格关键词（比如 gentle / kind / shy 等）
    personality_match = re.search(r"\b(gentle|kind|shy|cheerful|calm|serious|brave|cute|elegant|sweet|cool|happy|moody)\b", user_input, re.IGNORECASE)
    if personality_match:
        description.append({"Personality": personality_match.group(1).capitalize()})

    return description





def upload_to_imgbb(image_path: str) -> str:
    """
    Upload a local image to imgbb and return a publicly accessible URL.

    Args:
        image_path (str): Path to the image file.
        api_key (str): Your imgbb API key.

    Returns:
        str: URL of uploaded image or None if failed.
    """
    load_dotenv()
    api_key = os.getenv('UPLOAD_API_KEY')
    try:
        with open(image_path, "rb") as file:
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": api_key},
                files={"image": file}
            )
        result = response.json()
        if result.get("status") == 200:
            return result["data"]["url"]
        else:
            print("❌ Upload failed:", result.get("error"))
            return None
    except Exception as e:
        print("❌ Exception during upload:", str(e))
        return None



def convert_image_to_png(input_path, output_dir="converted", max_size=800):
    os.makedirs(output_dir, exist_ok=True)
    unique_name = f"{uuid4().hex}.png"
    output_path = os.path.join(output_dir, unique_name)

    with Image.open(input_path) as img:
        img = img.convert("RGB")

        # ✅ 强制裁剪为 3:4 居中
        width, height = img.size
        target_ratio = 3 / 4
        current_ratio = width / height

        if current_ratio > target_ratio:
            # 宽过长：裁剪左右
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        elif current_ratio < target_ratio:
            # 高过长：裁剪上下
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))
        # 如果正好是 3:4 就不需要裁剪

        # ✅ 缩放到标准尺寸（576x768）
        img = img.resize((576, 768))

        # 保存为 PNG
        img.save(output_path, "PNG")

    return output_path

def normalize_image_output(image_path, size=(512, 512)):
    """
    统一图像格式、尺寸，用于 Echomimic 输入。
    Args:
        image_path (str): 输入图像路径
        size (tuple): 输出图像尺寸 (width, height)
    Returns:
        str: 新图像保存路径
    """
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ 图片路径无效：{image_path}")

    img = Image.open(image_path).convert("RGB")
    img = img.resize(size)

    normalized_path = image_path.replace(".jpg", "_normalized.jpg").replace(".png", "_normalized.jpg")
    img.save(normalized_path, format="JPEG")

    print("🖼️ 已归一化图像保存为：", normalized_path)
    return normalized_path


def normalize_audio_output(audio_path, target_sample_rate=44100):
    """
    统一音频格式、采样率，用于 Echomimic 输入。
    Args:
        audio_path (str): 输入音频路径（如 mp3）
        target_sample_rate (int): 目标采样率，默认 44100 Hz
    Returns:
        str: 新音频保存路径（WAV格式）
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"❌ 音频路径无效：{audio_path}")

    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(target_sample_rate).set_channels(1)

    normalized_path = audio_path.replace(".mp3", "_normalized.wav").replace(".wav", "_normalized.wav")
    audio.export(normalized_path, format="wav")

    print("🎵 已归一化音频保存为：", normalized_path)
    return normalized_path

def extract_value_from_prompt(description_list, key="Name"):
    """
    从描述列表中提取指定key对应的值。
    Args:
        description_list (list): 角色描述，例如 [{"Name": "Airi"}, {"Gender": "Female"}]
        key (str): 需要提取的字段，默认是"Name"
    Returns:
        str or None: 提取到的值，找不到返回None
    """
    if not isinstance(description_list, list):
        return None

    for item in description_list:
        if isinstance(item, dict) and key in item:
            value = item[key]
            if isinstance(value, str):
                return value.strip().title()  # 标准化处理
            return value

    return None



# def restore_anime_face(input_path: str, output_path: str = None) -> str:
#     """
#     使用 Real-ESRGAN Anime 模型增强动漫图像（保持风格）
#     """
#     if not output_path:
#         output_path = input_path.replace(".png", "_restored.png")
#
#     model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
#                     num_block=23, num_grow_ch=32, scale=4)
#     upsampler = RealESRGANer(
#         scale=4,
#         model_path='weights/RealESRGAN_x4plus_anime_6B.pth',
#         model=model,
#         tile=0,
#         tile_pad=10,
#         pre_pad=0,
#         half=False
#     )
#
#     img = Image.open(input_path).convert("RGB")
#     output, _ = upsampler.enhance(np.array(img))
#     Image.fromarray(output).save(output_path)
#     return output_path

# if __name__ == "__main__":
#     input_img = "/Users/dingdingdingdingding/Desktop/HKU/sem2/SmartPhone/project/final project1/final project/assets/images/jessica_20250419_140420.jpg"
#     result_path = restore_anime_face(input_img)
#     print(f"Restored image saved to: {result_path}")