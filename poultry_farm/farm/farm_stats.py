"""Зведені метрики ферми."""
from dataclasses import dataclass


@dataclass
class FarmStats:
    """Зведені показники ферми для звіту."""
    employees: int
    birds: int
    unassigned: int
    by_species: dict
    avg_efficiency: float
    total_salary: float
