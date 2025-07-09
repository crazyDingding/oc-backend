import re
import json
import os
from typing import List, Dict

from utils.llms import OpenAI, DeepSeek, ElevenLabs
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env', override=True)
# from oscopilot.environments.py_env import PythonEnv
# from oscopilot.environments.py_jupyter_env import PythonJupyterEnv


MODEL_TYPE = os.getenv('MODEL_TYPE')


class BaseModule:
    def __init__(self, llm=None):
        """
        Initializes a new instance of BaseModule with an optional LLM instance.
        If no LLM is provided, a default one will be selected based on MODEL_TYPE.
        """
        if llm is not None:
            self.llm = llm
        else:
            # fallback to .env config
            MODEL_TYPE = os.getenv("MODEL_TYPE")
            if MODEL_TYPE == "OpenAI":
                self.llm = OpenAI()
            elif MODEL_TYPE == "DeepSeek":
                self.llm = DeepSeek()
            elif MODEL_TYPE == "ElevenLabs":
                self.llm = ElevenLabs()
            else:
                raise ValueError(f"Unsupported MODEL_TYPE: {MODEL_TYPE}")

        print(f"✅ Initialized LLM: {self.llm.model_name}")
        # self.environment = PythonEnv()
        # self.environment = PythonJupyterEnv()

    def extract_information(self, message, begin_str='[BEGIN]', end_str='[END]'):
        """
        Extracts substrings from a message that are enclosed within specified begin and end markers.

        Args:
            message (str): The message from which information is to be extracted.
            begin_str (str): The marker indicating the start of the information to be extracted.
            end_str (str): The marker indicating the end of the information to be extracted.

        Returns:
            list[str]: A list of extracted substrings found between the begin and end markers.
        """
        result = []
        _begin = message.find(begin_str)
        _end = message.find(end_str)
        while not (_begin == -1 or _end == -1):
            result.append(message[_begin + len(begin_str):_end].lstrip("\n"))
            message = message[_end + len(end_str):]
            _begin = message.find(begin_str)
            _end = message.find(end_str)
        return result

    def extract_json_from_string(self, text):
        """
        Identifies and extracts JSON data embedded within a given string.

        This method searches for JSON data within a string, specifically looking for
        JSON blocks that are marked with ```json``` notation. It attempts to parse
        and return the first JSON object found.

        Args:
            text (str): The text containing the JSON data to be extracted.

        Returns:
            dict: The parsed JSON data as a dictionary if successful.
            str: An error message indicating a parsing error or that no JSON data was found.
        """
        # Improved regular expression to find JSON data within a string
        json_regex = r'```json\n\s*\{\n\s*[\s\S\n]*\}\n\s*```'

        # Search for JSON data in the text
        matches = re.findall(json_regex, text)

        # Extract and parse the JSON data if found
        if matches:
            # Removing the ```json and ``` from the match to parse it as JSON
            json_data = matches[0].replace('```json', '').replace('```', '').strip()
            try:
                # Parse the JSON data
                parsed_json = json.loads(json_data)
                return parsed_json
            except json.JSONDecodeError as e:
                return f"Error parsing JSON data: {e}"
        else:
            return "No JSON data found in the string."

    def extract_list_from_string(self, text):
        """
        Extracts a list of task descriptions from a given string containing enumerated tasks.
        This function ensures that only text immediately following a numbered bullet is captured,
        and it stops at the first newline character or at the next number, preventing the inclusion of subsequent non-numbered lines or empty lines.

        Parameters:
        text (str): A string containing multiple enumerated tasks. Each task is numbered and followed by its description.

        Returns:
        list[str]: A list of strings, each representing the description of a task extracted from the input string.
        """

        # Regular expression pattern:
        # \d+\. matches one or more digits followed by a dot, indicating the task number.
        # \s+ matches one or more whitespace characters after the dot.
        # ([^\n]*?) captures any sequence of characters except newlines (non-greedy) as the task description.
        # (?=\n\d+\.|\n\Z|\n\n) is a positive lookahead that matches a position followed by either a newline with digits and a dot (indicating the start of the next task),
        # or the end of the string, or two consecutive newlines (indicating a break between tasks or end of content).
        task_pattern = r'\d+\.\s+([^\n]*?)(?=\n\d+\.|\n\Z|\n\n)'

        # Use the re.findall function to search for all matches of the pattern in the input text.
        data_list = re.findall(task_pattern, text)

        # Return the list of matched task descriptions.
        return data_list

    def extract_content_from_response(self, response):
        """
        Extracts the content from a response that contains either:
        - a valid JSON object (with a 'SampleSpeech' key)
        - or a single quoted string pretending to be a JSON object: {"..."}.

        Returns:
            dict or list: Parsed JSON content or {'SampleSpeech': "..."} fallback.
        """
        try:
            # 尝试提取大括号内容
            match = re.search(r'(\{.*?\})', response, re.DOTALL)
            if match:
                extracted = match.group(1)
                print("[Debug] Extracted JSON string:", extracted)
                try:
                    return json.loads(extracted)  # 尝试直接解析
                except json.JSONDecodeError:
                    # 尝试匹配 {"..."} 形式的句子
                    fallback_match = re.match(r'^\{\s*"?(.*?)"?\s*\}$', extracted)
                    if fallback_match:
                        fallback_text = fallback_match.group(1)
                        print("[Debug] Fallback extracted:", fallback_text)
                        return {"SampleSpeech": fallback_text.strip('"')}
                    return {"error": "Malformed JSON format"}
            else:
                return {"error": "No JSON found"}
        except Exception as e:
            return {"error": str(e)}



    def clean_and_parse_json(self, response):
        """
        Clean the response and parse it as JSON.

        This function removes any extra formatting (e.g., triple backticks) and ensures the content
        is valid JSON before parsing.

        :param response: The raw response string
        :return: Parsed JSON object or an error message
        """
        try:
            # 去掉可能的 ```json 和 ``` 标记
            clean_response = re.sub(r"```json|```", "", response).strip()

            # 打印清理后的响应，便于调试
            print("[Debug] Cleaned response for JSON parsing:\n", clean_response)

            # 尝试解析为 JSON
            parsed_json = json.loads(clean_response)
            return parsed_json
        except json.JSONDecodeError as e:
            # 如果解析失败，打印错误并返回空
            print("[Error] JSON decode error:", e)
            print("[Debug] Raw response causing error:\n", response)
            return None

    def transfer_data_to_prompt(self, data: List[Dict[str, str]]) -> str:
        """
        将 List[Dict] 转为自然段文本，确保 content 是字符串
        """
        if not data:
            return ""

        prompt_lines = []
        for item in data:
            for key, value in item.items():
                prompt_lines.append(f"{key}: {value}")

        return "\n".join(prompt_lines)  # ✅ 返回一个干净的字符串

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
