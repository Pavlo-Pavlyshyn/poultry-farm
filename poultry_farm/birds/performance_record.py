"""Запис показника ефективності."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PerformanceRecord:
    """Одне вимірювання показника ефективності птиці."""
    day: date
    value: float

    def to_dict(self) -> dict:
        return {"day": self.day.isoformat(), "value": self.value}

    @staticmethod
    def from_dict(data: dict) -> "PerformanceRecord":
        return PerformanceRecord(date.fromisoformat(data["day"]), float(data["value"]))
