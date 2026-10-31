"""Створення працівників за назвою посади."""
from ..errors import ValidationError
from .employee import Employee
from .manager import Manager
from .veterinarian import Veterinarian
from .worker import Worker


class EmployeeFactory:
    """Зіставляє назву типу з класом працівника (спрощений фабричний метод)."""
    TYPES = {cls.__name__: cls for cls in (Worker, Veterinarian, Manager)}

    @classmethod
    def labels(cls) -> dict:
        """Назви посад для меню: {тип: підпис}."""
        return {name: emp_cls.ROLE for name, emp_cls in cls.TYPES.items()}

    @classmethod
    def create(cls, kind: str, emp_id: int, name: str, base_salary: float) -> Employee:
        emp_cls = cls.TYPES.get(kind)
        if emp_cls is None:
            raise ValidationError(f"Невідома посада: {kind}")
        return emp_cls(emp_id, name, base_salary)

    @classmethod
    def from_dict(cls, data: dict) -> Employee:
        return cls.create(data["type"], data["id"], data["name"], data["base_salary"])
