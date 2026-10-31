"""Абстрактний працівник ферми."""
from abc import ABC, abstractmethod

from ..errors import ValidationError


class Employee(ABC):
    """Абстрактний працівник ферми."""
    ROLE = "Працівник"
    BONUS_PER_BIRD = 0.0

    def __init__(self, emp_id: int, name: str, base_salary: float):
        if not name.strip():
            raise ValidationError("Ім'я працівника не може бути порожнім")
        if base_salary < 0:
            raise ValidationError("Оклад не може бути від'ємним")
        self.id = emp_id
        self.name = name.strip()
        self.base_salary = float(base_salary)

    @property
    def role(self) -> str:
        return self.ROLE

    @abstractmethod
    def salary(self, bird_count: int, avg_efficiency: float) -> float:
        """Розрахунок місячної оплати з урахуванням закріпленої птиці."""

    def to_dict(self) -> dict:
        return {"type": type(self).__name__, "id": self.id,
                "name": self.name, "base_salary": self.base_salary}

    def __str__(self) -> str:
        return f"#{self.id} {self.name} ({self.role})"
