"""
FCC Hard Carbon Optimizer
=========================

A process optimization tool for producing hard carbon anode materials 
from FCC decant oil for sodium-ion batteries.

Targets the Goldilocks window: d002 = 0.37-0.40 nm

Installation:
    pip install fcc-hard-carbon

Quick Start:
    >>> from fcc_hard_carbon import HardCarbonPredictor, Feedstock, ProcessConditions
    >>> pred = HardCarbonPredictor()
    >>> feed = Feedstock(sulfur_wt_pct=3.5)
    >>> proc = ProcessConditions(temp_C=1100)
    >>> result = pred.predict(feed, proc)
    >>> print(f"d002: {result.d002_nm} nm, In Goldilocks: {result.in_goldilocks}")

CLI Usage:
    fcc-hard-carbon --sulfur 3.5 --temp 1100
    fcc-hard-carbon --optimize --samples 1000
    fcc-hard-carbon --economics --scenarios
"""

__version__ = "1.0.0"
__author__ = "FCC Hard Carbon Contributors"

from .models import (
    Feedstock,
    ProcessConditions,
    HardCarbonResult,
    HardCarbonPredictor,
    GoldilocksAnalyzer,
)

from .optimization import (
    ProcessOptimizer,
    SensitivityAnalyzer,
    OptResult,
    generate_contour_data,
)

from .economics import (
    EconomicsCalculator,
    PlantScale,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "Feedstock",
    "ProcessConditions", 
    "HardCarbonResult",
    "HardCarbonPredictor",
    "GoldilocksAnalyzer",
    # Optimization
    "ProcessOptimizer",
    "SensitivityAnalyzer",
    "OptResult",
    "generate_contour_data",
    # Economics
    "EconomicsCalculator",
    "PlantScale",
]
