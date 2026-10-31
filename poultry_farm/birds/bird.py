"""Абстрактна птиця."""
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from ..errors import ValidationError
from .performance_record import PerformanceRecord


class Bird(ABC):
    """Абстрактна птиця з обліком показників і відповідальним працівником."""
    SPECIES = "Птиця"
    METRIC = "Показник"
    UNIT = ""
    NORM = 1.0  # норма показника за одиницю обліку (для розрахунку ефективності)

    def __init__(self, bird_id: int, tag: str, birth_date: date,
                 weight_g: float, employee_id: Optional[int] = None,
                 records: Optional[list] = None):
        if not tag.strip():
            raise ValidationError("Бирка не може бути порожньою")
        if weight_g <= 0:
            raise ValidationError("Маса має бути додатною")
        if birth_date > date.today():
            raise ValidationError("Дата народження не може бути в майбутньому")
        self.id = bird_id
        self.tag = tag.strip()
        self.birth_date = birth_date
        self.weight_g = float(weight_g)
        self.employee_id = employee_id
        self.records: list[PerformanceRecord] = list(records or [])

    @property
    def species(self) -> str:
        return self.SPECIES

    def add_record(self, day: date, value: float) -> PerformanceRecord:
        if value < 0:
            raise ValidationError("Значення показника не може бути від'ємним")
        if day < self.birth_date:
            raise ValidationError("Дата запису раніше за дату народження")
        if day > date.today():
            raise ValidationError("Дата запису не може бути в майбутньому")
        rec = PerformanceRecord(day, float(value))
        self.records.append(rec)
        return rec

    def total(self) -> float:
        return sum(r.value for r in self.records)

    def average(self) -> float:
        return self.total() / len(self.records) if self.records else 0.0

    def efficiency(self) -> float:
        """Ефективність у відсотках від норми (середнє / норма * 100)."""
        return self.average() / self.NORM * 100

    def age_days(self, today: Optional[date] = None) -> int:
        return ((today or date.today()) - self.birth_date).days

    @abstractmethod
    def describe_metric(self) -> str:
        """Текстовий опис показника для звітів."""

    def to_dict(self) -> dict:
        return {"type": type(self).__name__, "id": self.id, "tag": self.tag,
                "birth_date": self.birth_date.isoformat(),
                "weight_g": self.weight_g, "employee_id": self.employee_id,
                "records": [r.to_dict() for r in self.records]}

    def __str__(self) -> str:
        return f"#{self.id} {self.species} [{self.tag}]"
