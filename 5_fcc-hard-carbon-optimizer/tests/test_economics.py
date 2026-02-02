"""Tests for Session 3: Economics"""
import sys
# Path handled by conftest.py

from fcc_hard_carbon import EconomicsCalculator, PlantScale

def test_capex():
    econ = EconomicsCalculator()
    capex = econ.get_capex()
    assert capex['total_cr'] > 0, "CAPEX should be positive"
    assert capex['installed_cr'] > capex['equipment_cr'], "Installed > Equipment"
    print(f"✅ CAPEX: ₹{capex['total_cr']:.1f} Cr (Equipment: ₹{capex['equipment_cr']:.1f} Cr)")

def test_opex():
    econ = EconomicsCalculator()
    opex = econ.get_opex()
    assert opex['total_cr'] > 0, "OPEX should be positive"
    assert opex['cost_per_kg'] > 0, "Cost/kg should be positive"
    print(f"✅ OPEX: ₹{opex['total_cr']:.2f} Cr/yr (₹{opex['cost_per_kg']:.1f}/kg)")

def test_revenue():
    econ = EconomicsCalculator()
    rev = econ.get_revenue()
    assert rev['revenue_cr'] > 0, "Revenue should be positive"
    assert 200 < rev['price_per_kg'] < 400, "Price should be realistic"
    print(f"✅ Revenue: ₹{rev['revenue_cr']:.2f} Cr/yr @ ₹{rev['price_per_kg']:.0f}/kg")

def test_npv_irr():
    econ = EconomicsCalculator()
    fin = econ.get_npv_irr()
    assert fin['npv_cr'] > 0, "NPV should be positive for viable project"
    assert fin['irr_pct'] > 12, "IRR should exceed discount rate"
    assert fin['payback_yr'] < 10, "Payback should be < project life"
    print(f"✅ NPV: ₹{fin['npv_cr']:.1f} Cr | IRR: {fin['irr_pct']:.1f}% | Payback: {fin['payback_yr']}yr")

def test_scenarios():
    econ = EconomicsCalculator()
    scen = econ.scenarios()
    assert len(scen) == 5, "Should have 5 scenarios"
    # NPV should increase with price
    npvs = [s['npv_cr'] for s in scen]
    assert npvs == sorted(npvs), "NPV should increase with price"
    print(f"✅ Scenarios: NPV range ₹{npvs[0]:.0f}-{npvs[-1]:.0f} Cr")

def test_scale_impact():
    econ_small = EconomicsCalculator(fcc_tpy=5000)
    econ_large = EconomicsCalculator(fcc_tpy=20000)
    
    npv_small = econ_small.get_npv_irr()['npv_cr']
    npv_large = econ_large.get_npv_irr()['npv_cr']
    
    assert npv_large > npv_small, "Larger scale should have higher NPV"
    print(f"✅ Scale: 5k TPY NPV=₹{npv_small:.0f}Cr vs 20k TPY NPV=₹{npv_large:.0f}Cr")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SESSION 3 TESTS - ECONOMICS")
    print("="*50 + "\n")
    
    test_capex()
    test_opex()
    test_revenue()
    test_npv_irr()
    test_scenarios()
    test_scale_impact()
    
    print("\n" + "="*50)
    print("ALL SESSION 3 TESTS PASSED ✅")
    print("="*50 + "\n")
