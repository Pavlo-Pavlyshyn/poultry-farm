"""Керівник зміни."""
from .employee import Employee


class Manager(Employee):
    """Керівник зміни: оклад + премія 10 % за ефективність не нижче 100 %."""
    ROLE = "Керівник зміни"
    PREMIUM_RATE = 0.10

    def salary(self, bird_count: int, avg_efficiency: float) -> float:
        bonus = self.PREMIUM_RATE * self.base_salary if avg_efficiency >= 100 else 0.0
        return self.base_salary + bonus
