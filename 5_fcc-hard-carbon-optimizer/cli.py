#!/usr/bin/env python3
"""FCC Hard Carbon Optimizer - Command Line Interface"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fcc_hard_carbon import (
    Feedstock, ProcessConditions, HardCarbonPredictor, GoldilocksAnalyzer,
    ProcessOptimizer, SensitivityAnalyzer, generate_contour_data,
    EconomicsCalculator
)

def main():
    p = argparse.ArgumentParser(description='FCC Hard Carbon Optimizer')
    
    # Feedstock
    p.add_argument('--sulfur', '-s', type=float, default=3.5, help='Sulfur wt%%')
    p.add_argument('--oxygen', '-o', type=float, default=1.0, help='Oxygen wt%%')
    p.add_argument('--aromatics', type=float, default=85, help='Aromatics %%')
    p.add_argument('--mcr', type=float, default=22, help='MCR wt%%')
    
    # Process
    p.add_argument('--temp', '-t', type=float, default=1100, help='Temperature °C')
    p.add_argument('--rate', '-r', type=float, default=5, help='Heating rate °C/min')
    p.add_argument('--time', type=float, default=2, help='Hold time hr')
    
    # Modes
    p.add_argument('--optimize', action='store_true', help='LHS optimization')
    p.add_argument('--sensitivity', action='store_true', help='Sensitivity analysis')
    p.add_argument('--contour', action='store_true', help='Contour map')
    p.add_argument('--sweep', action='store_true', help='Temp sweep')
    p.add_argument('--find-window', action='store_true', help='Goldilocks window')
    p.add_argument('--economics', action='store_true', help='Business case')
    p.add_argument('--scenarios', action='store_true', help='Price scenarios')
    
    # Options
    p.add_argument('--samples', type=int, default=1000, help='LHS samples')
    p.add_argument('--top', type=int, default=10, help='Top N results')
    p.add_argument('--fcc-tpy', type=float, default=10000, help='FCC oil TPY')
    p.add_argument('--yield-pct', type=float, default=35, help='Char yield %%')
    
    args = p.parse_args()
    
    # ===== ECONOMICS =====
    if args.economics or args.scenarios:
        print(f"\n{'='*65}")
        print("💰 FCC HARD CARBON - BUSINESS CASE")
        print(f"{'='*65}")
        
        econ = EconomicsCalculator(args.fcc_tpy, args.yield_pct)
        capex = econ.get_capex()
        opex = econ.get_opex()
        rev = econ.get_revenue()
        fin = econ.get_npv_irr()
        
        print(f"\n📦 SCALE: {args.fcc_tpy:,.0f} TPY FCC Oil → {rev['hc_tpy']:,.0f} TPY Hard Carbon ({args.yield_pct}% yield)")
        print(f"\n🏭 CAPEX: ₹{capex['total_cr']:.1f} Crore")
        print(f"⚙️ OPEX: ₹{opex['total_cr']:.2f} Crore/year (₹{opex['cost_per_kg']:.1f}/kg)")
        print(f"📈 REVENUE: ₹{rev['revenue_cr']:.2f} Crore/year @ ₹{rev['price_per_kg']:.0f}/kg")
        print(f"\n💵 NPV: ₹{fin['npv_cr']:.1f} Cr | IRR: {fin['irr_pct']:.1f}% | Payback: {fin['payback_yr']} yr")
        
        if args.scenarios:
            print(f"\n📊 PRICE SENSITIVITY:")
            print(f"{'Change':>8} | {'₹/kg':>6} | {'NPV':>8} | {'IRR':>6}")
            print("-"*40)
            for s in econ.scenarios():
                print(f"{s['change']:>8} | {s['price']:>6.0f} | {s['npv_cr']:>6.1f}Cr | {s['irr_pct']:>5.1f}%")
        
        print(f"\n{'='*65}\n")
        return
    
    feed = Feedstock(sulfur_wt_pct=args.sulfur, oxygen_wt_pct=args.oxygen,
                     aromatics_pct=args.aromatics, mcr_wt_pct=args.mcr)
    pred = HardCarbonPredictor()
    
    # ===== OPTIMIZE =====
    if args.optimize:
        print(f"\n{'='*70}")
        print("🎯 LATIN HYPERCUBE OPTIMIZATION")
        print(f"{'='*70}")
        print(f"Feedstock: S={feed.sulfur_wt_pct}% | Samples: {args.samples}")
        
        opt = ProcessOptimizer(feed)
        top = opt.optimize(args.samples, args.top)
        stats = opt.get_stats()
        
        print(f"\n📊 STATS: {stats['goldilocks']}/{stats['total']} in Goldilocks ({stats['rate_pct']:.1f}%)")
        
        if top:
            print(f"\n🏆 TOP {len(top)} CONDITIONS:")
            print(f"{'#':>2} | {'Temp':>6} | {'Rate':>5} | {'Time':>5} | {'d002':>7} | {'Cap':>5} | {'Score':>5}")
            print("-"*55)
            for i, r in enumerate(top, 1):
                print(f"{i:>2} | {r.temp_C:>6.0f} | {r.rate_C_min:>5.1f} | {r.time_hr:>5.2f} | {r.d002_nm:>7.4f} | {r.capacity:>5.0f} | {r.score:>5.1f}")
        print(f"{'='*70}\n")
        return
    
    # ===== SENSITIVITY =====
    if args.sensitivity:
        print(f"\n{'='*60}")
        print("📊 SENSITIVITY ANALYSIS (±20%)")
        print(f"{'='*60}")
        
        base = ProcessConditions(temp_C=args.temp, rate_C_min=args.rate, time_hr=args.time)
        sens = SensitivityAnalyzer(feed, base)
        results = sens.analyze()
        
        print(f"Base: T={args.temp}°C → d002={sens.base_d002:.4f}nm\n")
        print(f"{'Parameter':<15} | {'Δd002 Low':>10} | {'Δd002 High':>10} | {'Impact':>8}")
        print("-"*55)
        for r in results:
            print(f"{r['param']:<15} | {r['low']*1000:>+8.2f}mÅ | {r['high']*1000:>+8.2f}mÅ | {r['impact']*1000:>6.2f}mÅ")
        print(f"\n🔑 {results[0]['param']} has LARGEST impact")
        print(f"{'='*60}\n")
        return
    
    # ===== SWEEP =====
    if args.sweep:
        print(f"\n{'='*65}")
        print("TEMPERATURE SWEEP")
        print(f"{'='*65}")
        print(f"{'Temp':>6} | {'d002':>7} | {'Goldilocks':>10} | {'Cap':>6} | {'Score':>5}")
        print("-"*55)
        for T in range(900, 1301, 50):
            r = pred.predict(feed, ProcessConditions(temp_C=T, rate_C_min=args.rate, time_hr=args.time))
            gl = "✓ YES" if r.in_goldilocks else "  no"
            print(f"{T:>6} | {r.d002_nm:>7.4f} | {gl:>10} | {r.capacity_mAh_g:>6.1f} | {r.quality_score:>5.1f}")
        print(f"{'='*65}\n")
        return
    
    # ===== FIND WINDOW =====
    if args.find_window:
        analyzer = GoldilocksAnalyzer()
        w = analyzer.find_temp_window(feed, args.rate, args.time)
        print(f"\n{'='*55}")
        if w['optimal_temp']:
            print(f"✅ Goldilocks: {w['min_temp']}-{w['max_temp']}°C (optimal: {w['optimal_temp']}°C)")
        else:
            print("❌ No Goldilocks window found")
        print(f"{'='*55}\n")
        return
    
    # ===== DEFAULT: PREDICT =====
    proc = ProcessConditions(temp_C=args.temp, rate_C_min=args.rate, time_hr=args.time)
    r = pred.predict(feed, proc)
    
    print(f"\n{'='*55}")
    print("FCC HARD CARBON OPTIMIZER")
    print(f"{'='*55}")
    print(f"Feed: S={feed.sulfur_wt_pct}% | Proc: T={proc.temp_C}°C")
    print(f"\nd002: {r.d002_nm:.4f}nm {'✅ GOLDILOCKS' if r.in_goldilocks else '❌ OUTSIDE'}")
    print(f"Capacity: {r.capacity_mAh_g:.0f} mAh/g | ICE: {r.ice_pct:.1f}%")
    print(f"Score: {r.quality_score}/100 | Grade: {r.grade}")
    print(f"{'='*55}\n")

if __name__ == '__main__':
    main()
