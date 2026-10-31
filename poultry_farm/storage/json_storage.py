"""Збереження стану ферми між запусками (JSON)."""
import json
import os
import tempfile
from pathlib import Path

from ..errors import FarmError
from ..farm import Farm


class JsonStorage:
    """Читає і записує стан ферми у файл JSON."""

    def __init__(self, path):
        self.path = Path(path)

    def save(self, farm: Farm) -> None:
        """Атомарний запис: спершу тимчасовий файл, потім заміна."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(farm.to_dict(), f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def load(self) -> Farm:
        if not self.path.exists():
            return Farm()
        try:
            with open(self.path, encoding="utf-8") as f:
                return Farm.from_dict(json.load(f))
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise FarmError(f"Файл даних пошкоджено: {exc}") from exc
