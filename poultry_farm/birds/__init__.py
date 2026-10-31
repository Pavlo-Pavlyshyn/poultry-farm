"""Птиця та показники ефективності."""
from .bird import Bird
from .bird_factory import BirdFactory
from .broiler import Broiler
from .duck import Duck
from .laying_hen import LayingHen
from .performance_record import PerformanceRecord

__all__ = ["Bird", "BirdFactory", "Broiler", "Duck", "LayingHen", "PerformanceRecord"]
