"""Tests for Session 2: Optimization"""
import sys
# Path handled by conftest.py

from fcc_hard_carbon import Feedstock, ProcessConditions, HardCarbonPredictor
from fcc_hard_carbon import ProcessOptimizer, SensitivityAnalyzer, generate_contour_data

def test_lhs_optimization():
    """LHS optimization finds Goldilocks conditions"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    opt = ProcessOptimizer(feed)
    top = opt.optimize(n_samples=200, top_n=5)
    stats = opt.get_stats()
    
    assert stats['goldilocks'] > 0, "Should find some Goldilocks conditions"
    assert len(top) > 0, "Should return top conditions"
    assert all(r.in_goldilocks for r in top), "All top should be in Goldilocks"
    assert top[0].score >= top[-1].score, "Should be sorted by score"
    print(f"✅ LHS: Found {stats['goldilocks']}/{stats['total']} in Goldilocks, Top score={top[0].score:.1f}")

def test_sensitivity():
    """Sensitivity analysis identifies key parameters"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    proc = ProcessConditions(temp_C=1100)
    sens = SensitivityAnalyzer(feed, proc)
    results = sens.analyze()
    
    assert len(results) == 4, "Should analyze 4 parameters"
    assert results[0]['impact'] >= results[-1]['impact'], "Should be sorted by impact"
    # Sulfur or Temperature should be top
    assert results[0]['param'] in ['Sulfur', 'Temperature'], "Top should be Sulfur or Temperature"
    print(f"✅ Sensitivity: Top factor = {results[0]['param']} (impact={results[0]['impact']*1000:.1f}mÅ)")

def test_contour_data():
    """Contour data generation"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    data = generate_contour_data(feed, n=10)
    
    assert data['d002'].shape == (10, 10), "Grid should be 10x10"
    assert 0.335 <= data['d002'].min() <= 0.42, "d002 in valid range"
    assert 0.335 <= data['d002'].max() <= 0.42, "d002 in valid range"
    
    # Check Goldilocks region exists
    gl_count = ((data['d002'] >= 0.37) & (data['d002'] <= 0.40)).sum()
    assert gl_count > 0, "Goldilocks region should exist"
    print(f"✅ Contour: Generated {data['d002'].shape}, Goldilocks points={gl_count}")

def test_top_conditions_quality():
    """Top conditions should have d002 near optimal (0.385)"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    opt = ProcessOptimizer(feed)
    top = opt.optimize(n_samples=500, top_n=5)
    
    for r in top:
        assert abs(r.d002_nm - 0.385) < 0.01, f"d002={r.d002_nm} should be near 0.385"
        assert r.capacity >= 300, f"Top conditions should have capacity >= 300"
    print(f"✅ Top quality: All d002 within 0.01 of optimal, capacity >= 300")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SESSION 2 TESTS")
    print("="*50 + "\n")
    
    test_lhs_optimization()
    test_sensitivity()
    test_contour_data()
    test_top_conditions_quality()
    
    print("\n" + "="*50)
    print("ALL SESSION 2 TESTS PASSED ✅")
    print("="*50 + "\n")
