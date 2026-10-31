"""Птахівник."""
from .employee import Employee


class Worker(Employee):
    """Птахівник: оклад + доплата за кожну закріплену птицю."""
    ROLE = "Птахівник"
    BONUS_PER_BIRD = 15.0

    def salary(self, bird_count: int, avg_efficiency: float) -> float:
        return self.base_salary + self.BONUS_PER_BIRD * bird_count
