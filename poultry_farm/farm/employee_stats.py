"""Метрики одного працівника."""
from dataclasses import dataclass

from ..staff import Employee


@dataclass
class EmployeeStats:
    """Кількість закріпленої птиці, її середня ефективність і оплата працівника."""
    employee: Employee
    bird_count: int
    avg_efficiency: float
    salary: float
