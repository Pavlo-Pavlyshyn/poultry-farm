"""Курка-несучка."""
from .bird import Bird


class LayingHen(Bird):
    """Курка-несучка: показник — кількість яєць за день."""
    SPECIES = "Курка-несучка"
    METRIC = "Несучість"
    UNIT = "яєць/день"
    NORM = 0.85

    def describe_metric(self) -> str:
        return f"{self.METRIC}: всього {self.total():.0f} яєць, середня {self.average():.2f} {self.UNIT}"
