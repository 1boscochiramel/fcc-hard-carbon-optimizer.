"""FCC Hard Carbon Optimizer - Session 3: Economics"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PlantScale:
    fcc_oil_tpy: float = 10000
    char_yield_pct: float = 35
    
    @property
    def hc_tpy(self): return self.fcc_oil_tpy * self.char_yield_pct / 100

class EconomicsCalculator:
    """Complete economics: CAPEX, OPEX, NPV/IRR"""
    
    def __init__(self, fcc_tpy: float = 10000, yield_pct: float = 35):
        self.scale = PlantScale(fcc_tpy, yield_pct)
        
        # CAPEX (INR Crore)
        self.capex = {
            'furnace': 12.0, 'feed_system': 2.0, 'gas_handling': 2.5,
            'milling': 3.0, 'product_handling': 1.5, 'utilities': 2.0
        }
        self.install_factor = 1.35
        self.eng_pct = 0.12
        self.contingency_pct = 0.15
        
        # OPEX unit rates
        self.n2_rate = 12          # INR/kg
        self.n2_per_t = 80         # kg/t feed
        self.power_rate = 7        # INR/kWh
        self.power_per_t = 400     # kWh/t feed
        self.operators = 4 * 3     # per shift × shifts
        self.salary = 5            # LPA
        self.maint_pct = 0.03
        
        # Revenue (INR/kg HC)
        self.prices = {'premium': 350, 'standard': 280, 'offspec': 120}
        self.grade_mix = {'premium': 0.30, 'standard': 0.55, 'offspec': 0.15}
    
    def get_capex(self) -> Dict:
        equip = sum(self.capex.values())
        installed = equip * self.install_factor
        eng = installed * self.eng_pct
        cont = (installed + eng) * self.contingency_pct
        total = installed + eng + cont
        return {'equipment_cr': equip, 'installed_cr': round(installed, 1),
                'total_cr': round(total, 1)}
    
    def get_opex(self) -> Dict:
        s = self.scale
        n2 = s.fcc_oil_tpy * self.n2_per_t * self.n2_rate / 1e5        # Lakh
        power = s.fcc_oil_tpy * self.power_per_t * self.power_rate / 1e5
        labor = self.operators * self.salary
        maint = self.get_capex()['total_cr'] * 100 * self.maint_pct    # Cr→Lakh
        total = n2 + power + labor + maint
        cost_per_kg = total * 1e5 / (s.hc_tpy * 1000)
        return {'n2_lakh': round(n2,1), 'power_lakh': round(power,1),
                'labor_lakh': round(labor,1), 'maint_lakh': round(maint,1),
                'total_cr': round(total/100, 2), 'cost_per_kg': round(cost_per_kg, 1)}
    
    def get_revenue(self) -> Dict:
        blended = sum(self.prices[g] * self.grade_mix[g] for g in self.prices)
        hc_kg = self.scale.hc_tpy * 1000
        rev_cr = hc_kg * blended / 1e7
        return {'hc_tpy': self.scale.hc_tpy, 'price_per_kg': round(blended, 0),
                'revenue_cr': round(rev_cr, 2)}
    
    def get_npv_irr(self, rate: float = 0.12, years: int = 10, tax: float = 0.25) -> Dict:
        capex = self.get_capex()['total_cr']
        opex = self.get_opex()['total_cr']
        rev = self.get_revenue()['revenue_cr']
        
        ebitda = rev - opex
        depreciation = capex / years
        ebt = ebitda - depreciation
        net_income = ebt * (1 - tax) if ebt > 0 else ebt
        cf = net_income + depreciation
        
        cfs = [-capex] + [cf] * years
        npv = sum(c / (1 + rate)**t for t, c in enumerate(cfs))
        
        # IRR
        irr = self._irr(cfs)
        
        # Payback
        cum, payback = 0, years
        for t, c in enumerate(cfs):
            cum += c
            if cum >= 0:
                payback = t
                break
        
        return {'capex_cr': capex, 'ebitda_cr': round(ebitda, 2),
                'cash_flow_cr': round(cf, 2), 'npv_cr': round(npv, 1),
                'irr_pct': round(irr * 100, 1), 'payback_yr': payback}
    
    def _irr(self, cfs: List[float]) -> float:
        r = 0.1
        for _ in range(50):
            npv = sum(c / (1 + r)**t for t, c in enumerate(cfs))
            dnpv = sum(-t * c / (1 + r)**(t+1) for t, c in enumerate(cfs))
            if abs(dnpv) < 1e-10: break
            r -= npv / dnpv
        return max(0, min(r, 5))
    
    def scenarios(self) -> List[Dict]:
        """Price sensitivity: -20%, -10%, Base, +10%, +20%"""
        results = []
        base_price = self.get_revenue()['price_per_kg']
        
        for pct in [-20, -10, 0, 10, 20]:
            factor = 1 + pct/100
            # Temporarily adjust prices
            old_prices = self.prices.copy()
            self.prices = {k: v * factor for k, v in old_prices.items()}
            
            npv_irr = self.get_npv_irr()
            results.append({
                'change': f"{pct:+d}%",
                'price': round(base_price * factor, 0),
                'npv_cr': npv_irr['npv_cr'],
                'irr_pct': npv_irr['irr_pct'],
                'payback': npv_irr['payback_yr']
            })
            
            self.prices = old_prices
        return results
