# tools/character/manager.py

import random
from typing import Optional
from tools.prompts.default_descriptions import DEFAULT_DESCRIPTIONS


class CharacterPromptManager:
    def __init__(self, user_id: int, redis_client=None):
        self._default_descriptions = DEFAULT_DESCRIPTIONS.copy()
        self._shuffled_pool = self._default_descriptions.copy()
        random.shuffle(self._shuffled_pool)
        self._pointer = 0

        self.user_id = user_id
        self.redis = redis_client
        self.used_key = f"character:used:{user_id}"

    def _extract_name(self, description: list[dict], key: str = "Name") -> str:
        for item in description:
            if key in item and isinstance(item[key], str) and item[key].strip():
                return item[key].strip()
        return "unknown"

    def _has_used(self, name: str) -> bool:
        if self.redis:
            return self.redis.sismember(self.used_key, name)
        return False

    def _mark_used(self, name: str):
        if self.redis:
            self.redis.sadd(self.used_key, name)

    def _clear_used(self):
        if self.redis:
            self.redis.delete(self.used_key)

    def get_rotating_default_description(self) -> list[dict]:
        """
        从默认角色设定中轮换返回一个未使用过的设定，使用 Redis 记录去重
        """
        attempts = 0
        while attempts < len(self._shuffled_pool):
            if self._pointer >= len(self._shuffled_pool):
                random.shuffle(self._shuffled_pool)
                self._pointer = 0
            desc = self._shuffled_pool[self._pointer]
            self._pointer += 1
            name = self._extract_name(desc)

            if not self._has_used(name):
                self._mark_used(name)
                print(f"🎭 当前用户 {self.user_id} 使用默认角色：{name}")
                return desc

            attempts += 1

        # 如果所有角色都用过了，清空再来一轮
        print(f"♻️ 用户 {self.user_id} 的默认角色已轮完，重置轮换池")
        self._clear_used()
        self._pointer = 0
        random.shuffle(self._shuffled_pool)
        desc = self._shuffled_pool[self._pointer]
        self._pointer += 1
        name = self._extract_name(desc)
        self._mark_used(name)
        print(f"🎭 当前用户 {self.user_id} 使用默认角色：{name}")
        return desc

    def get_character_description(self, description) -> list[dict]:
        """
        若用户输入为空、非法或字段内容全为空，则返回默认角色设定（避免重复）
        """
        if not isinstance(description, list):
            print("⚠️ description 非 list，使用轮换默认角色设定")
            return self.get_rotating_default_description()

        if not description or all(
            not any(v.strip() for v in item.values() if isinstance(v, str))
            for item in description
        ):
            print("⚠️ description 为空或字段内容为空，使用轮换默认角色设定")
            return self.get_rotating_default_description()

        return description