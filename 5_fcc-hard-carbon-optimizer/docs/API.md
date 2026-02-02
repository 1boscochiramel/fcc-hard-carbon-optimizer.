# API Reference

## Core Classes

### `Feedstock`
Represents FCC decant oil feedstock properties.

```python
from fcc_hard_carbon import Feedstock

feed = Feedstock(
    sulfur_wt_pct=3.5,    # Sulfur content (1-6 wt%)
    oxygen_wt_pct=1.0,    # Oxygen content (0.5-3 wt%)
    aromatics_pct=85.0,   # Aromatic content (70-95%)
    mcr_wt_pct=22.0       # Micro Carbon Residue (15-35 wt%)
)
```

### `ProcessConditions`
Carbonization process parameters.

```python
from fcc_hard_carbon import ProcessConditions

proc = ProcessConditions(
    temp_C=1100,          # Temperature (900-1300°C)
    rate_C_min=5.0,       # Heating rate (1-20°C/min)
    time_hr=2.0,          # Hold time (0.5-4 hr)
    atmosphere='N2'       # Inert atmosphere
)
```

### `HardCarbonResult`
Prediction results with automatic Goldilocks classification.

```python
result = predictor.predict(feed, proc)

result.d002_nm          # Interlayer spacing (nm)
result.capacity_mAh_g   # Reversible capacity (mAh/g)
result.ice_pct          # Initial Coulombic Efficiency (%)
result.bet_m2_g         # BET surface area (m²/g)
result.yield_pct        # Char yield (%)
result.in_goldilocks    # True if d002 in 0.37-0.40 nm
result.quality_score    # 0-100 score
result.grade            # "Premium (A)", "Standard (B)", etc.
```

---

## Prediction

### `HardCarbonPredictor`

```python
from fcc_hard_carbon import HardCarbonPredictor

predictor = HardCarbonPredictor()

# Full prediction
result = predictor.predict(feed, proc)

# Individual properties
d002 = predictor.predict_d002(feed, proc)
capacity = predictor.predict_capacity(d002)
bet = predictor.predict_bet(proc)
ice = predictor.predict_ice(bet)
yield_pct = predictor.predict_yield(feed, proc)
```

### `GoldilocksAnalyzer`

```python
from fcc_hard_carbon import GoldilocksAnalyzer

analyzer = GoldilocksAnalyzer()

# Diagnose results
recommendations = analyzer.diagnose(result)
# Returns list of actionable recommendations

# Find temperature window for Goldilocks
window = analyzer.find_temp_window(feed, rate=5, time=2)
# Returns: {'min_temp': 850, 'max_temp': 1220, 'optimal_temp': 1035}
```

---

## Optimization

### `ProcessOptimizer`

```python
from fcc_hard_carbon import ProcessOptimizer

optimizer = ProcessOptimizer(
    feedstock=feed,
    temp_range=(900, 1300),
    rate_range=(1, 20),
    time_range=(0.5, 4),
    seed=42
)

# Run optimization
top_conditions = optimizer.optimize(
    n_samples=1000,   # LHS samples
    top_n=10          # Return top N results
)

# Get statistics
stats = optimizer.get_stats()
# {'total': 1000, 'goldilocks': 822, 'rate_pct': 82.2, ...}

# Access all results
all_results = optimizer.all_results
```

### `SensitivityAnalyzer`

```python
from fcc_hard_carbon import SensitivityAnalyzer

sens = SensitivityAnalyzer(feed, proc)

# Analyze ±20% variation
results = sens.analyze(pct=20)

# Returns list sorted by impact:
# [{'param': 'Sulfur', 'low': -0.0084, 'high': 0.0084, 'impact': 0.0168}, ...]

# Base d002 value
base_d002 = sens.base_d002
```

### `generate_contour_data`

```python
from fcc_hard_carbon import generate_contour_data

data = generate_contour_data(
    feed,
    temp_range=(900, 1300),
    sulfur_range=(1, 6),
    n=30  # Grid resolution
)

# Returns dict with:
data['temps']     # Temperature array
data['sulfurs']   # Sulfur array
data['d002']      # 2D d002 grid
data['capacity']  # 2D capacity grid
```

---

## Economics

### `EconomicsCalculator`

```python
from fcc_hard_carbon import EconomicsCalculator

econ = EconomicsCalculator(
    fcc_tpy=10000,    # FCC oil input (tonnes/year)
    yield_pct=35      # Char yield (%)
)

# CAPEX breakdown
capex = econ.get_capex()
# {'equipment_cr': 23.0, 'installed_cr': 31.1, 'total_cr': 40.0}

# OPEX breakdown
opex = econ.get_opex()
# {'n2_lakh': 96, 'power_lakh': 280, ..., 'cost_per_kg': 15.9}

# Revenue
rev = econ.get_revenue()
# {'hc_tpy': 3500, 'price_per_kg': 277, 'revenue_cr': 96.95}

# NPV/IRR
fin = econ.get_npv_irr(rate=0.12, years=10, tax=0.25)
# {'npv_cr': 352.9, 'irr_pct': 173.8, 'payback_yr': 1, ...}

# Price sensitivity scenarios
scenarios = econ.scenarios()
# [{'change': '-20%', 'npv_cr': 270.8, 'irr_pct': 137.5}, ...]
```

---

## CLI Reference

```bash
# Basic prediction
python cli.py --sulfur 3.5 --temp 1100

# All options
python cli.py \
    --sulfur 3.5 \
    --oxygen 1.0 \
    --temp 1100 \
    --rate 5 \
    --time 2 \
    --optimize \
    --samples 1000 \
    --top 10

# Modes
--optimize      # LHS optimization
--sensitivity   # Sensitivity analysis
--contour       # ASCII contour map
--sweep         # Temperature sweep
--find-window   # Find Goldilocks window
--economics     # Business case
--scenarios     # Price sensitivity
```
