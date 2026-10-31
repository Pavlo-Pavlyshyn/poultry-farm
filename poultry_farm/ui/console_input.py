"""Введення даних з консолі з перевіркою."""
from datetime import date
from typing import Optional

from ..errors import FarmError


class ConsoleInput:
    """Запити до користувача; некоректне введення перетворюється на FarmError."""

    @staticmethod
    def ask(prompt: str) -> str:
        return input(prompt).strip()

    @classmethod
    def ask_int(cls, prompt: str) -> int:
        try:
            return int(cls.ask(prompt))
        except ValueError:
            raise FarmError("Потрібно ввести ціле число") from None

    @classmethod
    def ask_optional_int(cls, prompt: str) -> Optional[int]:
        """Ціле число або None, якщо користувач натиснув Enter."""
        text = cls.ask(prompt)
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            raise FarmError("Потрібно ввести ціле число") from None

    @classmethod
    def ask_float(cls, prompt: str) -> float:
        try:
            return float(cls.ask(prompt).replace(",", "."))
        except ValueError:
            raise FarmError("Потрібно ввести число") from None

    @classmethod
    def ask_date(cls, prompt: str) -> date:
        text = cls.ask(prompt + " (РРРР-ММ-ДД, Enter — сьогодні): ")
        if not text:
            return date.today()
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise FarmError("Невірний формат дати") from None

    @classmethod
    def choose(cls, options: dict, title: str) -> str:
        """Показує нумерований перелік і повертає ключ вибраного варіанта."""
        keys = list(options)
        for i, k in enumerate(keys, 1):
            print(f"  {i}. {options[k]}")
        idx = cls.ask_int(f"{title}: ")
        if not 1 <= idx <= len(keys):
            raise FarmError("Немає такого варіанта")
        return keys[idx - 1]
