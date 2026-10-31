"""Ветеринар."""
from .employee import Employee


class Veterinarian(Employee):
    """Ветеринар: оклад + доплата за птицю, більша ставка."""
    ROLE = "Ветеринар"
    BONUS_PER_BIRD = 25.0

    def salary(self, bird_count: int, avg_efficiency: float) -> float:
        return self.base_salary + self.BONUS_PER_BIRD * bird_count
