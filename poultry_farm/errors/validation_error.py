"""Виняток для некоректних вхідних даних."""
from .farm_error import FarmError


class ValidationError(FarmError):
    """Некоректні вхідні дані."""
