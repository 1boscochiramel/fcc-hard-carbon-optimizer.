# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-02

### Added
- **Core Models** (Session 1)
  - `HardCarbonPredictor`: Predict d002, capacity, ICE, BET, yield
  - `GoldilocksAnalyzer`: Diagnose and recommend process adjustments
  - Feedstock and ProcessConditions data classes
  - Quality scoring and grading system

- **Optimization** (Session 2)
  - `ProcessOptimizer`: Latin Hypercube Sampling for parameter exploration
  - `SensitivityAnalyzer`: One-at-a-time sensitivity analysis
  - Contour data generation for visualization
  - Top N conditions ranking

- **Economics** (Session 3)
  - `EconomicsCalculator`: Complete business case analysis
  - CAPEX model: Equipment, installation, engineering, contingency
  - OPEX model: N2, power, labor, maintenance
  - NPV/IRR calculator with scenario analysis

- **Dashboard** (Session 4)
  - Streamlit web application with 5 interactive tabs
  - Real-time property prediction with Goldilocks gauge
  - Interactive Plotly visualizations
  - CSV export for optimization results

- **Distribution** (Session 5)
  - GitHub repository with CI/CD
  - Streamlit Cloud deployment
  - Comprehensive documentation

- **PyPI Package** (Session 6)
  - Published to PyPI: `pip install fcc-hard-carbon`
  - CLI entry point: `fcc-hard-carbon`
  - JSON output support: `--json` flag
  - Optional extras: `[dashboard]`, `[dev]`, `[all]`
  - Automated publishing via GitHub Actions

### CLI Features
```bash
fcc-hard-carbon --sulfur 3.5 --temp 1100           # Prediction
fcc-hard-carbon --optimize --samples 1000          # Optimization
fcc-hard-carbon --sensitivity                      # Sensitivity analysis
fcc-hard-carbon --economics --scenarios            # Business case
fcc-hard-carbon --json --sulfur 3.5 --temp 1100    # JSON output
```

### Technical Details
- Python 3.8+ compatible
- Dependencies: numpy, scipy
- Optional: pandas, plotly, streamlit (for dashboard)
- Test coverage: >90%

## [Unreleased]
- Additional feedstock models (petroleum pitch, biomass)
- DWSIM process simulation integration
- Multi-objective optimization
- Machine learning model calibration with experimental data
