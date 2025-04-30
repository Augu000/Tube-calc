from .calculator import ElectromagneticCalculator
from .physics import (
    SystemSpecs, MagnetSpecs, CoilSpecs, TubeSpecs,
    calculate_induced_voltage, calculate_induced_current,
    calculate_power, optimize_for_power
)

__all__ = [
    'ElectromagneticCalculator',
    'SystemSpecs',
    'MagnetSpecs',
    'CoilSpecs',
    'TubeSpecs',
    'calculate_induced_voltage',
    'calculate_induced_current',
    'calculate_power',
    'optimize_for_power'
] 