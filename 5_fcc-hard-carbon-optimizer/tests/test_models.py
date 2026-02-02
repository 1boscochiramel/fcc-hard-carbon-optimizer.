"""Tests for FCC Hard Carbon Optimizer"""
import sys
# Path handled by conftest.py

from fcc_hard_carbon import Feedstock, ProcessConditions, HardCarbonPredictor, GoldilocksAnalyzer

def test_d002_temperature_effect():
    """Higher temp → lower d002"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    pred = HardCarbonPredictor()
    
    d002_900 = pred.predict_d002(feed, ProcessConditions(temp_C=900))
    d002_1300 = pred.predict_d002(feed, ProcessConditions(temp_C=1300))
    
    assert d002_900 > d002_1300, f"Expected d002@900 > d002@1300, got {d002_900} vs {d002_1300}"
    print(f"✅ Temperature effect: d002@900={d002_900:.4f} > d002@1300={d002_1300:.4f}")

def test_d002_sulfur_effect():
    """Higher sulfur → higher d002"""
    pred = HardCarbonPredictor()
    proc = ProcessConditions(temp_C=1100)
    
    d002_low_s = pred.predict_d002(Feedstock(sulfur_wt_pct=2.0), proc)
    d002_high_s = pred.predict_d002(Feedstock(sulfur_wt_pct=5.0), proc)
    
    assert d002_high_s > d002_low_s, f"Expected high S > low S, got {d002_high_s} vs {d002_low_s}"
    print(f"✅ Sulfur effect: d002@S5%={d002_high_s:.4f} > d002@S2%={d002_low_s:.4f}")

def test_goldilocks_window():
    """Goldilocks = 0.37-0.40 nm"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    pred = HardCarbonPredictor()
    
    result = pred.predict(feed, ProcessConditions(temp_C=1100))
    
    assert 0.37 <= result.d002_nm <= 0.40, f"d002={result.d002_nm} outside Goldilocks"
    assert result.in_goldilocks, "in_goldilocks should be True"
    print(f"✅ Goldilocks check: d002={result.d002_nm:.4f}nm in [0.37, 0.40]")

def test_capacity_peaks_at_optimal():
    """Capacity peaks at d002=0.385"""
    pred = HardCarbonPredictor()
    
    cap_optimal = pred.predict_capacity(0.385)
    cap_low = pred.predict_capacity(0.35)
    cap_high = pred.predict_capacity(0.42)
    
    assert cap_optimal > cap_low, f"Cap@0.385 should > cap@0.35"
    assert cap_optimal > cap_high, f"Cap@0.385 should > cap@0.42"
    print(f"✅ Capacity peaks: {cap_optimal:.1f} > {cap_low:.1f} and {cap_high:.1f}")

def test_quality_grading():
    """Quality scoring and grading"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    pred = HardCarbonPredictor()
    
    result = pred.predict(feed, ProcessConditions(temp_C=1100))
    
    assert 0 <= result.quality_score <= 100, f"Score {result.quality_score} out of range"
    assert result.grade in ["Premium (A)", "Standard (B)", "Acceptable (C)", "Off-spec (D)"]
    print(f"✅ Quality: Score={result.quality_score}, Grade={result.grade}")

def test_find_temp_window():
    """Find Goldilocks temperature window"""
    feed = Feedstock(sulfur_wt_pct=3.5)
    analyzer = GoldilocksAnalyzer()
    
    window = analyzer.find_temp_window(feed)
    
    assert window['optimal_temp'] is not None, "Should find a window"
    assert window['min_temp'] < window['max_temp'], "min < max"
    print(f"✅ Temp window: {window['min_temp']}-{window['max_temp']}°C")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("FCC HARD CARBON OPTIMIZER - TESTS")
    print("="*50 + "\n")
    
    test_d002_temperature_effect()
    test_d002_sulfur_effect()
    test_goldilocks_window()
    test_capacity_peaks_at_optimal()
    test_quality_grading()
    test_find_temp_window()
    
    print("\n" + "="*50)
    print("ALL TESTS PASSED ✅")
    print("="*50 + "\n")
