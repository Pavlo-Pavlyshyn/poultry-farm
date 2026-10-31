"""Агрегат Farm: облік персоналу, птиці, закріплень і метрики."""
from datetime import date
from typing import Optional

from ..birds import Bird, BirdFactory
from ..errors import NotFoundError, ValidationError
from ..staff import Employee, EmployeeFactory
from .employee_stats import EmployeeStats
from .farm_stats import FarmStats


class Farm:
    """Ферма: зберігає працівників і птицю, підтримує цілісність закріплень."""

    def __init__(self, name: str = "Птахоферма"):
        self.name = name
        self.employees: dict[int, Employee] = {}
        self.birds: dict[int, Bird] = {}
        self._next_emp = 1
        self._next_bird = 1

    # -------------------------------------------------------------- персонал
    def add_employee(self, kind: str, name: str, base_salary: float) -> Employee:
        emp = EmployeeFactory.create(kind, self._next_emp, name, base_salary)
        self.employees[emp.id] = emp
        self._next_emp += 1
        return emp

    def get_employee(self, emp_id: int) -> Employee:
        try:
            return self.employees[emp_id]
        except KeyError:
            raise NotFoundError(f"Працівника #{emp_id} не знайдено") from None

    def remove_employee(self, emp_id: int) -> int:
        """Видаляє працівника; повертає кількість птиці, що стала без відповідального."""
        self.get_employee(emp_id)
        freed = 0
        for bird in self.birds.values():
            if bird.employee_id == emp_id:
                bird.employee_id = None
                freed += 1
        del self.employees[emp_id]
        return freed

    # ----------------------------------------------------------------- птиця
    def add_bird(self, kind: str, tag: str, birth_date: date, weight_g: float,
                 employee_id: Optional[int] = None) -> Bird:
        if any(b.tag == tag.strip() for b in self.birds.values()):
            raise ValidationError(f"Бирка «{tag}» уже використовується")
        if employee_id is not None:
            self.get_employee(employee_id)
        bird = BirdFactory.create(kind, self._next_bird, tag, birth_date, weight_g, employee_id)
        self.birds[bird.id] = bird
        self._next_bird += 1
        return bird

    def get_bird(self, bird_id: int) -> Bird:
        try:
            return self.birds[bird_id]
        except KeyError:
            raise NotFoundError(f"Птицю #{bird_id} не знайдено") from None

    def remove_bird(self, bird_id: int) -> None:
        self.get_bird(bird_id)
        del self.birds[bird_id]

    def assign(self, bird_id: int, employee_id: Optional[int]) -> None:
        """Закріплює птицю за працівником (None — зняти закріплення)."""
        bird = self.get_bird(bird_id)
        if employee_id is not None:
            self.get_employee(employee_id)
        bird.employee_id = employee_id

    def add_record(self, bird_id: int, day: date, value: float):
        return self.get_bird(bird_id).add_record(day, value)

    def birds_of(self, emp_id: int) -> list:
        return [b for b in self.birds.values() if b.employee_id == emp_id]

    # --------------------------------------------------------------- метрики
    def employee_stats(self, emp_id: int) -> EmployeeStats:
        emp = self.get_employee(emp_id)
        birds = [b for b in self.birds_of(emp_id) if b.records]
        avg = sum(b.efficiency() for b in birds) / len(birds) if birds else 0.0
        count = len(self.birds_of(emp_id))
        return EmployeeStats(emp, count, avg, emp.salary(count, avg))

    def all_employee_stats(self) -> list:
        return sorted((self.employee_stats(i) for i in self.employees),
                      key=lambda s: s.avg_efficiency, reverse=True)

    def stats(self) -> FarmStats:
        by_species: dict[str, int] = {}
        for b in self.birds.values():
            by_species[b.species] = by_species.get(b.species, 0) + 1
        measured = [b for b in self.birds.values() if b.records]
        avg = sum(b.efficiency() for b in measured) / len(measured) if measured else 0.0
        return FarmStats(
            employees=len(self.employees), birds=len(self.birds),
            unassigned=sum(1 for b in self.birds.values() if b.employee_id is None),
            by_species=by_species, avg_efficiency=avg,
            total_salary=sum(s.salary for s in self.all_employee_stats()))

    def top_birds(self, n: int = 5) -> list:
        measured = [b for b in self.birds.values() if b.records]
        return sorted(measured, key=lambda b: b.efficiency(), reverse=True)[:n]

    # ---------------------------------------------------------- серіалізація
    def to_dict(self) -> dict:
        return {"name": self.name, "next_emp": self._next_emp, "next_bird": self._next_bird,
                "employees": [e.to_dict() for e in self.employees.values()],
                "birds": [b.to_dict() for b in self.birds.values()]}

    @staticmethod
    def from_dict(data: dict) -> "Farm":
        farm = Farm(data.get("name", "Птахоферма"))
        for e in data.get("employees", []):
            emp = EmployeeFactory.from_dict(e)
            farm.employees[emp.id] = emp
        for b in data.get("birds", []):
            bird = BirdFactory.from_dict(b)
            farm.birds[bird.id] = bird
        farm._next_emp = data.get("next_emp", max(farm.employees, default=0) + 1)
        farm._next_bird = data.get("next_bird", max(farm.birds, default=0) + 1)
        return farm
