"""Створення птиці за назвою виду."""
from datetime import date
from typing import Optional

from ..errors import ValidationError
from .bird import Bird
from .broiler import Broiler
from .duck import Duck
from .laying_hen import LayingHen
from .performance_record import PerformanceRecord


class BirdFactory:
    """Зіставляє назву типу з класом птиці (спрощений фабричний метод)."""
    TYPES = {cls.__name__: cls for cls in (LayingHen, Broiler, Duck)}

    @classmethod
    def labels(cls) -> dict:
        """Назви видів для меню: {тип: підпис}."""
        return {name: bird_cls.SPECIES for name, bird_cls in cls.TYPES.items()}

    @classmethod
    def create(cls, kind: str, bird_id: int, tag: str, birth_date: date, weight_g: float,
               employee_id: Optional[int] = None, records: Optional[list] = None) -> Bird:
        bird_cls = cls.TYPES.get(kind)
        if bird_cls is None:
            raise ValidationError(f"Невідомий вид птиці: {kind}")
        return bird_cls(bird_id, tag, birth_date, weight_g, employee_id, records)

    @classmethod
    def from_dict(cls, data: dict) -> Bird:
        records = [PerformanceRecord.from_dict(r) for r in data.get("records", [])]
        return cls.create(data["type"], data["id"], data["tag"],
                          date.fromisoformat(data["birth_date"]), data["weight_g"],
                          data.get("employee_id"), records)
