"""Виняток для відсутнього об'єкта."""
from .farm_error import FarmError


class NotFoundError(FarmError):
    """Об'єкт із заданим ідентифікатором не знайдено."""
