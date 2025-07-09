from datetime import datetime
from typing import AsyncGenerator

import openai
import logging
import os
import time
import requests
import json
import openai
from dotenv import load_dotenv
from openai import OpenAI as DeepSeekClient, AsyncOpenAI
from openai import OpenAI as KimiClient
from elevenlabs.client import ElevenLabs as ElevenLabsClient
from requests import RequestException, ReadTimeout
from tqdm import tqdm

from utils.utils import upload_to_imgbb, convert_image_to_png

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')
DS_API_KEY = os.getenv('DS_API_KEY')
KIMI_API_KEY = os.getenv('KIMI_API_KEY')
VOICE_API_KEY = os.getenv('VOICE_API_KEY')
SD_API_KEY = os.getenv('SD_API_KEY')


OPENAI_ORGANIZATION = os.getenv('OPENAI_ORGANIZATION')

BASE_URL = os.getenv('OPENAI_BASE_URL')
CONNECTION_STRING = os.getenv('CONNECTION_STRING')

proxies = {
            "http": os.getenv('HTTP_PROXY'),
            "https": os.getenv('HTTPS_PROXY'),
            "all": os.getenv('ALL_PROXY')
}
# add
MODEL_SERVER = os.getenv('MODEL_SERVER')

import openai
import os
import logging
import requests

client = AsyncOpenAI()
class OpenAI:
    """
    A class for interacting with the OpenAI API, allowing for chat completion requests.

    This class simplifies the process of sending requests to OpenAI's chat model by providing
    a convenient interface for the chat completion API. It handles setting up the API key
    and organization for the session and provides a method to send chat messages.

    Attributes:
        model_name (str): The name of the model to use for chat completions. Default is set
                          by the global `MODEL_NAME`.
        api_key (str): The API key used for authentication with the OpenAI API. This should
                       be set through the `OPENAI_API_KEY` global variable.
        organization (str): The organization ID for OpenAI. Set this through the
                            `OPENAI_ORGANIZATION` global variable.
    """

    def __init__(self):
        """
        Initializes the OpenAI object with the given configuration.
        """
        MODEL_NAME = os.getenv('MODEL_NAME')
        self.model_name = MODEL_NAME
        self.api_key = os.getenv('OPENAI_API_KEY')  # Ensure the API key is loaded
        self.proxies = proxies or {}
        if not self.api_key:
            raise ValueError("API key is not provided.")
        openai.api_key = self.api_key
        self.client = AsyncOpenAI()

    async def chat(self, messages, temperature=0, prefix=""):
        """
        Sends a chat completion request to the OpenAI API using the specified messages and parameters.

        Args:
            messages (list of dict): A list of message dictionaries, where each dictionary
                                     should contain keys like 'role' and 'content' to
                                     specify the role (e.g., 'system', 'user') and content of
                                     each message.
            temperature (float, optional): Controls randomness in the generation. Lower values
                                           make the model more deterministic. Defaults to 0.

        Returns:
            str: The content of the first message in the response from the OpenAI API.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature
            )
            content = response.choices[0].message.content

            if len(prefix) > 0 and prefix[-1] != " ":
                prefix += " "
            logging.info(f"{prefix}Response: {content}")

            return content

        except requests.exceptions.RequestException as e:
            logging.error(f"APIConnectionError: {e}")
            return None

    def set_model_name(self, model_name):
        self.model_name = model_name



class DeepSeek:
    """
    A class for interacting with the OpenAI API, allowing for chat completion requests.

    This class simplifies the process of sending requests to OpenAI's chat model by providing
    a convenient interface for the chat completion API. It handles setting up the API key
    and organization for the session and provides a method to send chat messages.

    Attributes:
        model_name (str): The name of the model to use for chat completions. Default is set
                          by the global `MODEL_NAME`.
        api_key (str): The API key used for authentication with the OpenAI API. This should
                       be set through the `OPENAI_API_KEY` global variable.
        organization (str): The organization ID for OpenAI. Set this through the
                            `OPENAI_ORGANIZATION` global variable.
    """

    def __init__(self):
        """
        Initializes the OpenAI object with the given configuration.
        """
        MODEL_NAME = os.getenv('DS_MODEL_NAME')
        self.model_name = MODEL_NAME

        self.api_key = DS_API_KEY
        self.client = DeepSeekClient(api_key=self.api_key, base_url="https://api.deepseek.com")


    def chat(self, messages, temperature=0, prefix=""):
        """
        Sends a chat completion request to the DeepSeek API.

        Args:
            messages (list of dict): A list of message dicts, e.g., {"role": "user", "content": "..."}
            temperature (float): Sampling randomness (default 0)
            prefix (str): Optional logging prefix

        Returns:
            str: The response content from DeepSeek
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature
        )

        if prefix and not prefix.endswith(" "):
            prefix += " "

        logging.info(f"{prefix}DeepSeek response: {response.choices[0].message.content}")
        return response.choices[0].message.content

    def set_model_name(self, model_name):
        self.model_name = model_name


class Kimi:
    """
    A class for interacting with the Moonshot (Kimi) API, supporting both standard and partial (role-playing) modes.
    """

    def __init__(self):
        MODEL_NAME = os.getenv('KIMI_MODEL_NAME')
        API_KEY = os.getenv('KIMI_API_KEY')
        self.model_name = MODEL_NAME
        self.api_key = API_KEY
        self.client = KimiClient(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        )

    async def chat(self, messages: list[dict], temperature=0.3, prefix="") -> str:
        """
        Sends a batch of messages to the Kimi API (non-streaming).
        Args:
            messages (list): Full conversation history.
            temperature (float): Controls randomness.
            prefix (str): Prefix for logging.
        Returns:
            str: The generated response content.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=4096
        )

        content = response.choices[0].message.content

        if prefix and not prefix.endswith(" "):
            prefix += " "
        logging.info(f"{prefix}Kimi response: {content}")

        return content

    def chat_stream(self, messages: list[dict], temperature=0.3):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
            stream=True
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def chat_stream_async(self, messages: list[dict], temperature=0.3):
        for token in self.chat_stream(messages, temperature):
            yield token  # 在 async def 中直接 yield → 是合法 async generator


class ElevenLabs:
    """
    A class for interacting with the ElevenLabs TTS API using the official SDK.

    This class simplifies the process of converting text to speech using ElevenLabs voices,
    supporting multilingual synthesis, emotional tone, and audio customization.

    Attributes:
        api_key (str): Your ElevenLabs API key, loaded from the `ELEVENLABS_API_KEY` environment variable.
        voice_id (str): The voice ID to be used for synthesis, from `ELEVENLABS_VOICE_ID` env.
        model_id (str): The model ID (e.g., 'eleven_monolingual_v1' or 'eleven_multilingual_v2').
        output_format (str): Format of the generated audio file (e.g., 'mp3_44100_128').
    """

    def __init__(self):
        """
        Initializes the ElevenLabs object with API credentials and voice/model configuration.
        """
        MODEL_NAME = os.getenv('VOICE_MODEL_NAME')
        self.api_key = VOICE_API_KEY
        self.model_id = MODEL_NAME
        self.voice_id = os.getenv("VOICE_ID")  # 默认 Rachel
        self.output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT")

        self.client = ElevenLabsClient(api_key=self.api_key)

    def synthesize(self, text, character_name="default", output_path=None):
        logging.info(f"[ElevenLabs] Synthesizing text: {text[:30]}...")

        try:
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                output_format=self.output_format,
                text=text,
                model_id=self.model_id
            )

            audio_bytes = b"".join(audio)

            if output_path is None:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                output_dir = os.path.join(project_root, "assets", "audios")
                os.makedirs(output_dir, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{character_name.lower()}_{timestamp}.mp3"
                output_path = os.path.join(output_dir, filename)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logging.info(f"[ElevenLabs] Audio saved to: {output_path}")
            return output_path

        except Exception as e:
            logging.error(f"[ElevenLabs] Synthesis failed: {str(e)}")
            return None

    def set_voice_id(self, voice_id):
        """
        Dynamically set a different voice_id.
        """
        self.voice_id = voice_id

class StableDiffusion:
    """
    A class for interacting with the Modelslab.com Stable Diffusion API.

    Supports both text-to-image (text2img) and image-to-image (img2img) generation.

    Attributes:
        api_key (str): Your Modelslab API key, from SD_API_KEY environment variable.
        model_id (str): The model ID to use (e.g., 'revAnimated_v122').
        mode (str): 'text2img' or 'img2img'.
    """

    def __init__(self, mode="text2img"):
        MODEL_NAME = os.getenv('SD_MODEL_NAME')
        self.api_key = SD_API_KEY
        self.model_id = MODEL_NAME
        self.mode = mode
        print(f"✅ self.api_key = {self.api_key} (length={len(self.api_key) if self.api_key else 0})")
        self.endpoint = {
            "text2img": "https://modelslab.com/api/v6/images/text2img",
            "img2img": "https://modelslab.com/api/v6/images/img2img"
        }.get(mode)

        if not self.endpoint:
            raise ValueError("mode must be 'text2img' or 'img2img'")

    def generate(
            self,
            prompt,
            character_name="default",
            init_image_url=None,
            output_path=None,
            max_retries=30,
            retry_delay=6,
            request_timeout=60,  # 新增：请求超时阈值（秒）
            post_retry=1
    ):
        logging.info(f"[StableDiffusion] Generating {self.mode} for {character_name}...")

        payload = {
            "key": self.api_key,
            "model_id": self.model_id,
            "prompt": prompt,
            "negative_prompt": "ugly, blurry, distorted, bad anatomy, extra limbs, deformed",
            "width": "576",
            "height": "768",
            "samples": "1",
            "num_inference_steps": "30",
            "safety_checker": "no",
            "enhance_prompt": "yes",
            "seed": None,
            "guidance_scale": 7.5,
            "multi_lingual": "no",
            "panorama": "no",
            "self_attention": "no",
            "upscale": "no",
            "lora_model": None,
            "tomesd": "yes",
            "use_karras_sigmas": "yes",
            "vae": None,
            "lora_strength": None,
            "scheduler": "UniPCMultistepScheduler",
            "webhook": None,
            "track_id": None
        }

        # img2img 额外参数
        if self.mode == "img2img":
            if not init_image_url:
                raise ValueError("init_image_url is required for img2img mode.")
            payload["init_image"] = init_image_url
            payload["strength"] = 0.7

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"  # 防止被 Cloudflare 拦截
        }

        # --- 第一次请求 + ReadTimeout 重试 ---
        for attempt in range(post_retry + 1):
            try:
                print(f"[Attempt {attempt + 1}] POST to {self.endpoint} (timeout={request_timeout}s)")
                resp = requests.post(
                    self.endpoint,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=request_timeout
                )
                result = resp.json()
                break  # 成功拿到 result，跳出重试循环

            except ReadTimeout:
                logging.warning(f"[StableDiffusion] Request timed out on attempt {attempt + 1}.")
                if attempt == post_retry:
                    logging.error("[StableDiffusion] All retries exhausted. Aborting.")
                    return None
                time.sleep(2)  # 小的间隔后再试

            except RequestException as e:
                logging.error(f"[StableDiffusion] Request failed: {e}")
                return None

        print("📦 Raw API Response:", result)

        # --- ① 立即成功 ---
        if result.get("status") == "success":
            image_url = result["output"][0]
            # ✅ 先保存本地
            self._download_image(image_url, character_name, output_path)
            # 🎯 直接返回远端 URL
            return image_url

        # --- ② 后台处理，轮询 fetch_result ---
        if result.get("status") == "processing" and result.get("fetch_result"):
            fetch_url = result["fetch_result"]
            logging.info(f"[StableDiffusion] processing, will fetch: {fetch_url}")
            for i in range(1, max_retries + 1):
                time.sleep(retry_delay)
                try:
                    fr = requests.get(fetch_url, headers=headers, timeout=request_timeout).json()
                except Exception as e:
                    logging.warning(f"[Fetch] attempt {i} error: {e}")
                    continue

                status = fr.get("status")
                logging.info(f"[Fetch] attempt {i}/{max_retries}, status={status}")
                if status == "success":
                    image_url = fr["output"][0]
                    # ✅ 先保存本地
                    self._download_image(image_url, character_name, output_path)
                    # 🎯 再返回远端 URL
                    return image_url
                if status not in ("processing", "error"):
                    break

            logging.error("[StableDiffusion] fetch loop exhausted without success")
            return None

            # 其他错误
        msg = result.get("message") or result.get("messege") or "Unknown error"
        logging.error(f"[StableDiffusion] Generation failed: {msg}")
        return None

    @staticmethod
    def build_front_facing_prompt(description: list) -> str:
        """
        构建一个适合 Stable Diffusion 的正脸人物 prompt，基于 description 字段提取信息。

        Args:
            description (list[dict]): 角色设定，例如：
                [{"Name": "Jessica"}, {"Gender": "Female"}, {"Personality": "Gentle"}, {"Appearance": "silver hair"}]

        Returns:
            str: 用于图像生成的 prompt 字符串
        """
        # 转换为标准 dict：{"name": "Jessica", "gender": "Female", ...}
        info = {k.lower(): v for d in description for k, v in d.items()}

        name = info.get("name", "a character")
        gender = info.get("gender", "").lower()
        mood = info.get("personality", "gentle").lower()
        appearance = info.get("appearance", "").strip()

        context_text = gender + " " + appearance

        # —— 根据外观内容判断角色类型 ——
        if any(word in context_text for word in ["cat", "fox", "wolf", "furry", "ears", "tail"]):
            gender_prefix = "furry character"
        elif any(word in context_text for word in ["beast", "dragon", "creature", "monster"]):
            gender_prefix = "fantasy creature"
        elif any(word in context_text for word in ["robot", "ai", "android", "cyber"]):
            gender_prefix = "android"
        elif any(word in gender for word in ["female", "girl", "woman", "lady"]):
            gender_prefix = "girl"
        elif any(word in gender for word in ["male", "boy", "man", "gentleman"]):
            gender_prefix = "boy"
        else:
            gender_prefix = "character"

        # —— 若 appearance 中未含穿着关键词，补全默认衣着以防裸露 ——
        clothing_keywords = ["dress", "skirt", "suit", "kimono", "uniform", "robe", "jacket", "coat", "clothes",
                             "wearing", "outfit"]
        if not any(word in appearance.lower() for word in clothing_keywords):
            appearance += ", wearing an elegant outfit with long sleeves"

        prompt = (
            f"((masterpiece)), ((best quality)), ((ultra-detailed)), "
            f"portrait of a {mood} anime {gender_prefix} named {name}, "
            f"{appearance + ',' if appearance else ''} "
            f"(extremely beautiful symmetrical face:1.3), "
            f"((sharp nose)), ((defined lips)), ((realistic mouth)), ((detailed facial features)), ((fine nose shadow)), ((clear lip texture)), "
            f"(facing camera:1.4), (looking directly at viewer:1.4), "
            f"(head and shoulders only), (centered composition), "
            f"studio ghibli style, soft lighting, 4k, high resolution, "
            f"((modest clothing)), ((no nudity)), ((no cleavage)), ((no revealing outfits)), "
            f"((no visible undergarments)), ((no sexually suggestive pose)), ((fully clothed)), "
            f"((safe for work)), ((clean background)), ((elegant outfit)), ((non-revealing))"
        )
        return prompt

    def _download_image(self, image_url, character_name="default", output_path=None, max_retries=10, retry_delay=3):
        # ✅ 替换转义符
        image_url = image_url.replace("\\/", "/")
        print(f"[Debug] Cleaned image_url = {image_url}")

        if output_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            output_dir = os.path.join(project_root, "assets", "images")
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{character_name.lower()}_{timestamp}.jpg"
            output_path = os.path.join(output_dir, filename)

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        for attempt in tqdm(range(1, max_retries + 1), desc="⏳ Waiting for image to be ready", unit="try"):
            try:
                response = requests.get(image_url, headers=headers, stream=True, timeout=15)
                content_type = response.headers.get("Content-Type", "")
                print(f"[Debug] Attempt {attempt}/{max_retries} - Content-Type: {content_type}")

                if "image" in content_type:
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    logging.info(f"[StableDiffusion] ✅ Image saved to: {output_path}")
                    return output_path

                print(f"[⏳] Not ready yet, waiting {retry_delay}s...")
                time.sleep(retry_delay)

            except Exception as e:
                logging.error(f"[StableDiffusion] ❌ Download failed (attempt {attempt}): {str(e)}")
                time.sleep(retry_delay)

        logging.error("[StableDiffusion] ❌ Image download failed after max retries.")
        return None

def main():
    # start_time = time.time()
    # # messages = [{'role': 'system',
    # #              'content': 'You are a Original Charactor Designer, please generate some dialog that fits the gentle characterization'},
    # #             {'role': 'user', 'content': "Hello"}]
    # # message.append({"role": "user", "content": 'hello'})
    # # print(OPENAI_API_KEY)
    # # print(BASE_URL)
    # llm =ElevenLabs()
    # print("model_name", llm.model_id)
    # print("api_key", llm.api_key)
    #
    # # 待合成文本
    # text = "Hello, Senpai~ Would you like to read something together?"
    #
    # # 合成并保存音频
    # output_path = llm.synthesize(text)
    #
    # print("✅ 音频已保存到：", output_path)
    # # response = llm.chat(messages)
    # # print(response)
    # end_time = time.time()
    # execution_time = end_time - start_time
    # # print(f"生成的单词数: {len(response)}")
    # print(f"程序执行时间: {execution_time}秒")
    start_time = time.time()

    # 示例角色描述
    description = [
        {"Name": "Jessica"},
        {"Gender": "Female"},
        {"Personality": "Gentle"}
    ]

    # 初始化模型（文生图）
    sd = StableDiffusion(mode="text2img")
    print("🧠 使用模型:", sd.model_id)
    print("🔑 API Key:", sd.api_key[:6] + "..." if sd.api_key else "None")

    # 生成 prompt
    prompt = sd.build_front_facing_prompt(description)
    character_name = next((d["Name"] for d in description if "Name" in d), "default")

    print("🎨 开始生成图像...")
    result_path = sd.generate(prompt=prompt, character_name=character_name)

    if result_path:
        print("✅ 图像保存成功：", result_path)
    else:
        print("❌ 图像生成失败")

    print(f"⏱️ 执行时间: {round(time.time() - start_time, 2)} 秒")

def test_img2img_generation():
    start_time = time.time()

    # 示例角色描述
    description = [
        {"Name": "Jessica"},
        {"Gender": "Female"},
        {"Personality": "Gentle"}
    ]

    # TODO：替换路径
    converted_path = convert_image_to_png("/Users/dingdingdingdingding/Desktop/HKU/sem2/Project/final project/assets/images/yemi.jpg")

    # 上传图片到 imgbb 并获取公网 URL
    init_image_url = upload_to_imgbb(converted_path)

    if not init_image_url:
        print("❌ 图片上传失败，无法进行图生图任务")
        return

    # 初始化 StableDiffusion（图生图模式）
    sd = StableDiffusion(mode="img2img")
    print("🧠 使用模型:", sd.model_id)
    print("🔑 API Key:", sd.api_key[:6] + "..." if sd.api_key else "None")

    # 构造 prompt
    prompt = sd.build_front_facing_prompt(description)
    character_name = next((d["Name"] for d in description if "Name" in d), "default")

    # 开始生成图像
    print("🎨 开始图生图生成...")
    result_path = sd.generate(prompt=prompt, character_name=character_name, init_image_url=init_image_url)

    if result_path:
        print("✅ 图像保存成功：", result_path)
    else:
        print("❌ 图像生成失败")

    print(f"⏱️ 执行时间: {round(time.time() - start_time, 2)} 秒")


if __name__ == '__main__':
    test_img2img_generation()