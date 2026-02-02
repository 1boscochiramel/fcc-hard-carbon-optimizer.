"""FCC Hard Carbon Optimizer - Core Models"""
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional
import numpy as np

# ============== DATA CLASSES ==============

@dataclass
class Feedstock:
    """FCC Decant Oil Feedstock"""
    sulfur_wt_pct: float = 3.5
    oxygen_wt_pct: float = 1.0
    aromatics_pct: float = 85.0
    mcr_wt_pct: float = 22.0
    name: str = "FCC Decant Oil"
    
    def __post_init__(self):
        assert 0.5 <= self.sulfur_wt_pct <= 8, f"Sulfur {self.sulfur_wt_pct} out of range"
        assert 0 <= self.oxygen_wt_pct <= 5, f"Oxygen {self.oxygen_wt_pct} out of range"

@dataclass
class ProcessConditions:
    """Carbonization Process Parameters"""
    temp_C: float = 1100
    rate_C_min: float = 5.0
    time_hr: float = 2.0
    atmosphere: str = 'N2'
    
    def __post_init__(self):
        assert 800 <= self.temp_C <= 1500, f"Temp {self.temp_C} out of range"
        assert 0.5 <= self.rate_C_min <= 50, f"Rate {self.rate_C_min} out of range"
        assert 0.25 <= self.time_hr <= 10, f"Time {self.time_hr} out of range"

@dataclass
class HardCarbonResult:
    """Predicted Hard Carbon Properties"""
    d002_nm: float
    capacity_mAh_g: float
    ice_pct: float
    bet_m2_g: float
    yield_pct: float
    in_goldilocks: bool = field(init=False)
    quality_score: float = field(init=False)
    grade: str = field(init=False)
    
    def __post_init__(self):
        self.in_goldilocks = 0.37 <= self.d002_nm <= 0.40
        self._calc_score()
        self._calc_grade()
    
    def _calc_score(self):
        """Quality score 0-100"""
        score = 0
        # d002 score (40 pts) - peak at 0.385
        d002_dist = abs(self.d002_nm - 0.385)
        score += max(0, 40 * (1 - d002_dist / 0.05))
        # Capacity score (30 pts)
        score += min(30, self.capacity_mAh_g / 10)
        # ICE score (20 pts)
        score += min(20, (self.ice_pct - 60) / 1.5) if self.ice_pct > 60 else 0
        # Yield score (10 pts)
        score += min(10, self.yield_pct / 4)
        self.quality_score = round(score, 1)
    
    def _calc_grade(self):
        if self.quality_score >= 80 and self.in_goldilocks:
            self.grade = "Premium (A)"
        elif self.quality_score >= 65 and self.in_goldilocks:
            self.grade = "Standard (B)"
        elif self.quality_score >= 50:
            self.grade = "Acceptable (C)"
        else:
            self.grade = "Off-spec (D)"

# ============== PREDICTORS ==============

class HardCarbonPredictor:
    """
    Predict hard carbon properties from feedstock + process.
    
    Key physics:
    - Higher temp → lower d002 (more graphitic)
    - Higher sulfur → higher d002 (crosslinking prevents ordering)
    - Higher heating rate → higher d002 (kinetic disorder)
    
    GOLDILOCKS WINDOW: d002 = 0.37-0.40 nm for Na-ion
    """
    
    # d002 coefficients (calibrate with your Paper 5 data)
    D002 = {
        'base': 0.335,      # graphite baseline
        'temp': -3.5e-5,    # per °C above 1000
        'sulfur': 0.012,    # per wt% S
        'oxygen': 0.006,    # per wt% O
        'rate': 0.0006,     # per °C/min
        'time': -0.004,     # per hour
    }
    
    # Capacity peaks at optimal d002
    CAP = {'peak': 320, 'optimal_d002': 0.385, 'sigma': 0.018, 'base': 80}
    
    # ICE decreases with BET surface area
    ICE = {'max': 92, 'slope': -1.0, 'min': 55}
    
    # BET depends on process severity
    BET = {'base': 40, 'temp': -0.025, 'rate': 0.4, 'time': -3}
    
    # Yield depends on feedstock
    YLD = {'base': 20, 'mcr': 0.6, 'arom': 0.12, 'temp': -0.008}
    
    def predict_d002(self, feed: Feedstock, proc: ProcessConditions) -> float:
        """Predict interlayer spacing (nm)"""
        d = self.D002
        d002 = (d['base'] + 
                d['temp'] * (proc.temp_C - 1000) +
                d['sulfur'] * feed.sulfur_wt_pct +
                d['oxygen'] * feed.oxygen_wt_pct +
                d['rate'] * proc.rate_C_min +
                d['time'] * proc.time_hr)
        return np.clip(d002, 0.335, 0.42)
    
    def predict_capacity(self, d002: float) -> float:
        """Predict reversible capacity (mAh/g) from d002"""
        c = self.CAP
        cap = c['base'] + (c['peak'] - c['base']) * np.exp(
            -((d002 - c['optimal_d002'])**2) / (2 * c['sigma']**2))
        return cap
    
    def predict_bet(self, proc: ProcessConditions) -> float:
        """Predict BET surface area (m²/g)"""
        b = self.BET
        bet = (b['base'] + 
               b['temp'] * (proc.temp_C - 1000) +
               b['rate'] * proc.rate_C_min +
               b['time'] * proc.time_hr)
        return np.clip(bet, 1, 80)
    
    def predict_ice(self, bet: float) -> float:
        """Predict Initial Coulombic Efficiency (%)"""
        i = self.ICE
        ice = i['max'] + i['slope'] * bet
        return np.clip(ice, i['min'], i['max'])
    
    def predict_yield(self, feed: Feedstock, proc: ProcessConditions) -> float:
        """Predict char yield (wt%)"""
        y = self.YLD
        yld = (y['base'] + 
               y['mcr'] * feed.mcr_wt_pct +
               y['arom'] * feed.aromatics_pct +
               y['temp'] * (proc.temp_C - 1000))
        return np.clip(yld, 15, 50)
    
    def predict(self, feed: Feedstock, proc: ProcessConditions) -> HardCarbonResult:
        """Run all predictions"""
        d002 = self.predict_d002(feed, proc)
        bet = self.predict_bet(proc)
        return HardCarbonResult(
            d002_nm=round(d002, 4),
            capacity_mAh_g=round(self.predict_capacity(d002), 1),
            ice_pct=round(self.predict_ice(bet), 1),
            bet_m2_g=round(bet, 1),
            yield_pct=round(self.predict_yield(feed, proc), 1)
        )

# ============== GOLDILOCKS ANALYZER ==============

class GoldilocksAnalyzer:
    """Analyze results against Goldilocks window (d002 = 0.37-0.40 nm)"""
    
    D002_MIN, D002_MAX, D002_OPT = 0.37, 0.40, 0.385
    CAP_MIN, ICE_MIN, YLD_MIN = 200, 70, 20
    
    def diagnose(self, result: HardCarbonResult) -> List[str]:
        """Return actionable recommendations"""
        recs = []
        
        # d002 diagnosis
        if result.d002_nm < self.D002_MIN:
            recs.append(f"❌ d002 too LOW ({result.d002_nm:.4f}nm) → Lower temp OR increase sulfur OR faster heating")
        elif result.d002_nm > self.D002_MAX:
            recs.append(f"❌ d002 too HIGH ({result.d002_nm:.4f}nm) → Higher temp OR longer hold time OR slower heating")
        else:
            recs.append(f"✅ d002 IN GOLDILOCKS ({result.d002_nm:.4f}nm)")
        
        # Capacity
        if result.capacity_mAh_g < self.CAP_MIN:
            recs.append(f"⚠️ Capacity low ({result.capacity_mAh_g:.0f} mAh/g) → Optimize d002 toward {self.D002_OPT}nm")
        else:
            recs.append(f"✅ Capacity OK ({result.capacity_mAh_g:.0f} mAh/g)")
        
        # ICE
        if result.ice_pct < self.ICE_MIN:
            recs.append(f"⚠️ ICE low ({result.ice_pct:.1f}%) → Higher temp to reduce BET surface area")
        else:
            recs.append(f"✅ ICE OK ({result.ice_pct:.1f}%)")
        
        return recs
    
    def find_temp_window(self, feed: Feedstock, rate: float = 5, time: float = 2) -> Dict:
        """Find temperature range that hits Goldilocks"""
        predictor = HardCarbonPredictor()
        goldilocks_temps = []
        
        for T in range(850, 1350, 10):
            proc = ProcessConditions(temp_C=T, rate_C_min=rate, time_hr=time)
            d002 = predictor.predict_d002(feed, proc)
            if self.D002_MIN <= d002 <= self.D002_MAX:
                goldilocks_temps.append(T)
        
        if goldilocks_temps:
            return {
                'min_temp': min(goldilocks_temps),
                'max_temp': max(goldilocks_temps),
                'optimal_temp': (min(goldilocks_temps) + max(goldilocks_temps)) // 2,
                'window_width': max(goldilocks_temps) - min(goldilocks_temps)
            }
        return {'min_temp': None, 'max_temp': None, 'optimal_temp': None, 'window_width': 0}
