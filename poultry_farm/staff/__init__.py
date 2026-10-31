"""Персонал ферми."""
from .employee import Employee
from .employee_factory import EmployeeFactory
from .manager import Manager
from .veterinarian import Veterinarian
from .worker import Worker

__all__ = ["Employee", "EmployeeFactory", "Manager", "Veterinarian", "Worker"]
