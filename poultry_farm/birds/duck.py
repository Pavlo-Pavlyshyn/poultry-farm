"""Качка."""
from .bird import Bird


class Duck(Bird):
    """Качка: показник — кількість яєць за день."""
    SPECIES = "Качка"
    METRIC = "Несучість"
    UNIT = "яєць/день"
    NORM = 0.70

    def describe_metric(self) -> str:
        return f"{self.METRIC}: всього {self.total():.0f} яєць, середня {self.average():.2f} {self.UNIT}"
