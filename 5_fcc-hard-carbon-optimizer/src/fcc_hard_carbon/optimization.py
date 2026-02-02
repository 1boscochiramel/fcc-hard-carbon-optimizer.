"""FCC Hard Carbon Optimizer - Session 2: Optimization Engine"""
import numpy as np
from scipy.stats import qmc
from typing import List, Dict, Tuple
from dataclasses import dataclass
import pandas as pd

from .models import Feedstock, ProcessConditions, HardCarbonPredictor

@dataclass
class OptResult:
    """Optimization result"""
    temp_C: float
    rate_C_min: float
    time_hr: float
    d002_nm: float
    capacity: float
    ice_pct: float
    yield_pct: float
    score: float
    grade: str
    in_goldilocks: bool

class ProcessOptimizer:
    """Find optimal process conditions via Latin Hypercube Sampling"""
    
    def __init__(self, feedstock: Feedstock, temp_range=(900,1300), rate_range=(1,20), time_range=(0.5,4), seed=42):
        self.feed = feedstock
        self.temp_range = temp_range
        self.rate_range = rate_range
        self.time_range = time_range
        self.seed = seed
        self.predictor = HardCarbonPredictor()
        self.all_results: List[OptResult] = []
    
    def optimize(self, n_samples: int = 1000, top_n: int = 10) -> List[OptResult]:
        """Run LHS optimization and return top N Goldilocks conditions"""
        sampler = qmc.LatinHypercube(d=3, seed=self.seed)
        unit = sampler.random(n_samples)
        
        temps = self.temp_range[0] + unit[:,0] * (self.temp_range[1] - self.temp_range[0])
        rates = self.rate_range[0] + unit[:,1] * (self.rate_range[1] - self.rate_range[0])
        times = self.time_range[0] + unit[:,2] * (self.time_range[1] - self.time_range[0])
        
        self.all_results = []
        for t, r, h in zip(temps, rates, times):
            pc = ProcessConditions(temp_C=t, rate_C_min=r, time_hr=h)
            res = self.predictor.predict(self.feed, pc)
            self.all_results.append(OptResult(
                temp_C=round(t,1), rate_C_min=round(r,1), time_hr=round(h,2),
                d002_nm=res.d002_nm, capacity=res.capacity_mAh_g, ice_pct=res.ice_pct,
                yield_pct=res.yield_pct, score=res.quality_score, grade=res.grade,
                in_goldilocks=res.in_goldilocks
            ))
        
        goldilocks = sorted([r for r in self.all_results if r.in_goldilocks], 
                           key=lambda x: x.score, reverse=True)
        return goldilocks[:top_n]
    
    def get_stats(self) -> Dict:
        gl = [r for r in self.all_results if r.in_goldilocks]
        return {
            'total': len(self.all_results), 'goldilocks': len(gl),
            'rate_pct': len(gl)/len(self.all_results)*100 if self.all_results else 0,
            'best_score': max((r.score for r in gl), default=0),
            'best_cap': max((r.capacity for r in gl), default=0)
        }

class SensitivityAnalyzer:
    """One-at-a-time sensitivity analysis for d002"""
    
    def __init__(self, feedstock: Feedstock, base_proc: ProcessConditions):
        self.feed = feedstock
        self.base = base_proc
        self.pred = HardCarbonPredictor()
        self.base_d002 = self.pred.predict_d002(feedstock, base_proc)
    
    def analyze(self, pct: float = 20) -> List[Dict]:
        """Analyze ±pct% variation in each parameter"""
        results = []
        
        # Temperature
        low = self.base.temp_C * (1 - pct/100)
        high = self.base.temp_C * (1 + pct/100)
        d_low = self.pred.predict_d002(self.feed, ProcessConditions(temp_C=low, rate_C_min=self.base.rate_C_min, time_hr=self.base.time_hr))
        d_high = self.pred.predict_d002(self.feed, ProcessConditions(temp_C=high, rate_C_min=self.base.rate_C_min, time_hr=self.base.time_hr))
        results.append({'param': 'Temperature', 'low': d_low - self.base_d002, 'high': d_high - self.base_d002})
        
        # Heating rate
        low = max(1, self.base.rate_C_min * (1 - pct/100))
        high = min(20, self.base.rate_C_min * (1 + pct/100))
        d_low = self.pred.predict_d002(self.feed, ProcessConditions(temp_C=self.base.temp_C, rate_C_min=low, time_hr=self.base.time_hr))
        d_high = self.pred.predict_d002(self.feed, ProcessConditions(temp_C=self.base.temp_C, rate_C_min=high, time_hr=self.base.time_hr))
        results.append({'param': 'Heating Rate', 'low': d_low - self.base_d002, 'high': d_high - self.base_d002})
        
        # Hold time
        low = max(0.5, self.base.time_hr * (1 - pct/100))
        high = min(6, self.base.time_hr * (1 + pct/100))
        d_low = self.pred.predict_d002(self.feed, ProcessConditions(temp_C=self.base.temp_C, rate_C_min=self.base.rate_C_min, time_hr=low))
        d_high = self.pred.predict_d002(self.feed, ProcessConditions(temp_C=self.base.temp_C, rate_C_min=self.base.rate_C_min, time_hr=high))
        results.append({'param': 'Hold Time', 'low': d_low - self.base_d002, 'high': d_high - self.base_d002})
        
        # Sulfur
        low = max(1, self.feed.sulfur_wt_pct * (1 - pct/100))
        high = min(6, self.feed.sulfur_wt_pct * (1 + pct/100))
        d_low = self.pred.predict_d002(Feedstock(sulfur_wt_pct=low), self.base)
        d_high = self.pred.predict_d002(Feedstock(sulfur_wt_pct=high), self.base)
        results.append({'param': 'Sulfur', 'low': d_low - self.base_d002, 'high': d_high - self.base_d002})
        
        # Sort by impact
        for r in results:
            r['impact'] = abs(r['high'] - r['low'])
        results.sort(key=lambda x: x['impact'], reverse=True)
        return results

def generate_contour_data(feed: Feedstock, temp_range=(900,1300), sulfur_range=(1,6), n=30):
    """Generate grid data for contour plots"""
    pred = HardCarbonPredictor()
    temps = np.linspace(temp_range[0], temp_range[1], n)
    sulfurs = np.linspace(sulfur_range[0], sulfur_range[1], n)
    
    d002 = np.zeros((n, n))
    cap = np.zeros((n, n))
    
    for i, s in enumerate(sulfurs):
        for j, t in enumerate(temps):
            r = pred.predict(Feedstock(sulfur_wt_pct=s, oxygen_wt_pct=feed.oxygen_wt_pct), 
                            ProcessConditions(temp_C=t))
            d002[i,j] = r.d002_nm
            cap[i,j] = r.capacity_mAh_g
    
    return {'temps': temps, 'sulfurs': sulfurs, 'd002': d002, 'capacity': cap}
