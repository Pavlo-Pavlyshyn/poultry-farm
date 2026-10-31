"""Бройлер."""
from .bird import Bird


class Broiler(Bird):
    """Бройлер: показник — добовий приріст маси у грамах."""
    SPECIES = "Бройлер"
    METRIC = "Приріст маси"
    UNIT = "г/день"
    NORM = 55.0

    def describe_metric(self) -> str:
        return f"{self.METRIC}: всього {self.total():.0f} г, середній {self.average():.1f} {self.UNIT}"
