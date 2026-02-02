#!/usr/bin/env python3
"""
FCC Hard Carbon Optimizer - Command Line Interface

Usage:
    fcc-hard-carbon --sulfur 3.5 --temp 1100
    fcc-hard-carbon --optimize --samples 1000
    fcc-hard-carbon --economics --scenarios
"""
import argparse
import sys

from .models import Feedstock, ProcessConditions, HardCarbonPredictor, GoldilocksAnalyzer
from .optimization import ProcessOptimizer, SensitivityAnalyzer
from .economics import EconomicsCalculator


def main():
    """Main entry point for CLI."""
    p = argparse.ArgumentParser(
        prog='fcc-hard-carbon',
        description='FCC Hard Carbon Optimizer - Na-ion Battery Anode Material',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fcc-hard-carbon --sulfur 3.5 --temp 1100       # Single prediction
  fcc-hard-carbon --optimize --samples 1000      # Find optimal conditions
  fcc-hard-carbon --sensitivity                  # Parameter sensitivity
  fcc-hard-carbon --economics --scenarios        # Business case analysis
        """
    )
    
    # Version
    p.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    # Feedstock
    feed_group = p.add_argument_group('Feedstock Properties')
    feed_group.add_argument('--sulfur', '-s', type=float, default=3.5,
                           help='Sulfur content (wt%%), default: 3.5')
    feed_group.add_argument('--oxygen', '-o', type=float, default=1.0,
                           help='Oxygen content (wt%%), default: 1.0')
    feed_group.add_argument('--aromatics', type=float, default=85,
                           help='Aromatic content (%%), default: 85')
    feed_group.add_argument('--mcr', type=float, default=22,
                           help='Micro Carbon Residue (wt%%), default: 22')
    
    # Process
    proc_group = p.add_argument_group('Process Conditions')
    proc_group.add_argument('--temp', '-t', type=float, default=1100,
                           help='Carbonization temperature (°C), default: 1100')
    proc_group.add_argument('--rate', '-r', type=float, default=5,
                           help='Heating rate (°C/min), default: 5')
    proc_group.add_argument('--time', type=float, default=2,
                           help='Hold time (hr), default: 2')
    
    # Modes
    mode_group = p.add_argument_group('Analysis Modes')
    mode_group.add_argument('--optimize', action='store_true',
                           help='Run Latin Hypercube optimization')
    mode_group.add_argument('--sensitivity', action='store_true',
                           help='Run sensitivity analysis')
    mode_group.add_argument('--sweep', action='store_true',
                           help='Temperature sweep')
    mode_group.add_argument('--find-window', action='store_true',
                           help='Find Goldilocks temperature window')
    mode_group.add_argument('--economics', action='store_true',
                           help='Business case analysis')
    mode_group.add_argument('--scenarios', action='store_true',
                           help='Price scenario analysis')
    
    # Options
    opt_group = p.add_argument_group('Options')
    opt_group.add_argument('--samples', type=int, default=1000,
                          help='LHS samples for optimization, default: 1000')
    opt_group.add_argument('--top', type=int, default=10,
                          help='Top N results to show, default: 10')
    opt_group.add_argument('--fcc-tpy', type=float, default=10000,
                          help='FCC oil input (tonnes/year), default: 10000')
    opt_group.add_argument('--yield-pct', type=float, default=35,
                          help='Char yield (%%), default: 35')
    opt_group.add_argument('--json', action='store_true',
                          help='Output results as JSON')
    
    args = p.parse_args()
    
    # JSON output helper
    if args.json:
        import json
        
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                import numpy as np
                if isinstance(obj, (np.bool_, bool)):
                    return bool(obj)
                if isinstance(obj, (np.integer, int)):
                    return int(obj)
                if isinstance(obj, (np.floating, float)):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)
        
        def output(data):
            print(json.dumps(data, indent=2, cls=NumpyEncoder))
    else:
        output = None
    
    # ===== ECONOMICS =====
    if args.economics or args.scenarios:
        econ = EconomicsCalculator(args.fcc_tpy, args.yield_pct)
        capex = econ.get_capex()
        opex = econ.get_opex()
        rev = econ.get_revenue()
        fin = econ.get_npv_irr()
        
        if args.json:
            data = {
                'scale': {'fcc_tpy': args.fcc_tpy, 'hc_tpy': rev['hc_tpy'], 'yield_pct': args.yield_pct},
                'capex': capex, 'opex': opex, 'revenue': rev, 'financial': fin
            }
            if args.scenarios:
                data['scenarios'] = econ.scenarios()
            output(data)
        else:
            print(f"\n{'='*65}")
            print("💰 FCC HARD CARBON - BUSINESS CASE")
            print(f"{'='*65}")
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
        return 0
    
    # Create feedstock and predictor
    feed = Feedstock(sulfur_wt_pct=args.sulfur, oxygen_wt_pct=args.oxygen,
                     aromatics_pct=args.aromatics, mcr_wt_pct=args.mcr)
    pred = HardCarbonPredictor()
    
    # ===== OPTIMIZE =====
    if args.optimize:
        opt = ProcessOptimizer(feed)
        top = opt.optimize(args.samples, args.top)
        stats = opt.get_stats()
        
        if args.json:
            output({
                'stats': stats,
                'top_conditions': [
                    {'temp_C': r.temp_C, 'rate_C_min': r.rate_C_min, 'time_hr': r.time_hr,
                     'd002_nm': r.d002_nm, 'capacity': r.capacity, 'score': r.score}
                    for r in top
                ]
            })
        else:
            print(f"\n{'='*70}")
            print("🎯 LATIN HYPERCUBE OPTIMIZATION")
            print(f"{'='*70}")
            print(f"Feedstock: S={feed.sulfur_wt_pct}% | Samples: {args.samples}")
            print(f"\n📊 STATS: {stats['goldilocks']}/{stats['total']} in Goldilocks ({stats['rate_pct']:.1f}%)")
            
            if top:
                print(f"\n🏆 TOP {len(top)} CONDITIONS:")
                print(f"{'#':>2} | {'Temp':>6} | {'Rate':>5} | {'Time':>5} | {'d002':>7} | {'Cap':>5} | {'Score':>5}")
                print("-"*55)
                for i, r in enumerate(top, 1):
                    print(f"{i:>2} | {r.temp_C:>6.0f} | {r.rate_C_min:>5.1f} | {r.time_hr:>5.2f} | {r.d002_nm:>7.4f} | {r.capacity:>5.0f} | {r.score:>5.1f}")
            print(f"{'='*70}\n")
        return 0
    
    # ===== SENSITIVITY =====
    if args.sensitivity:
        base = ProcessConditions(temp_C=args.temp, rate_C_min=args.rate, time_hr=args.time)
        sens = SensitivityAnalyzer(feed, base)
        results = sens.analyze()
        
        if args.json:
            output({'base_d002': sens.base_d002, 'sensitivity': results})
        else:
            print(f"\n{'='*60}")
            print("📊 SENSITIVITY ANALYSIS (±20%)")
            print(f"{'='*60}")
            print(f"Base: T={args.temp}°C → d002={sens.base_d002:.4f}nm\n")
            print(f"{'Parameter':<15} | {'Δd002 Low':>10} | {'Δd002 High':>10} | {'Impact':>8}")
            print("-"*55)
            for r in results:
                print(f"{r['param']:<15} | {r['low']*1000:>+8.2f}mÅ | {r['high']*1000:>+8.2f}mÅ | {r['impact']*1000:>6.2f}mÅ")
            print(f"\n🔑 {results[0]['param']} has LARGEST impact")
            print(f"{'='*60}\n")
        return 0
    
    # ===== SWEEP =====
    if args.sweep:
        if args.json:
            results = []
            for T in range(900, 1301, 50):
                r = pred.predict(feed, ProcessConditions(temp_C=T, rate_C_min=args.rate, time_hr=args.time))
                results.append({'temp': T, 'd002': r.d002_nm, 'in_goldilocks': r.in_goldilocks,
                               'capacity': r.capacity_mAh_g, 'score': r.quality_score})
            output(results)
        else:
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
        return 0
    
    # ===== FIND WINDOW =====
    if args.find_window:
        analyzer = GoldilocksAnalyzer()
        w = analyzer.find_temp_window(feed, args.rate, args.time)
        
        if args.json:
            output(w)
        else:
            print(f"\n{'='*55}")
            if w['optimal_temp']:
                print(f"✅ Goldilocks: {w['min_temp']}-{w['max_temp']}°C (optimal: {w['optimal_temp']}°C)")
            else:
                print("❌ No Goldilocks window found")
            print(f"{'='*55}\n")
        return 0
    
    # ===== DEFAULT: PREDICT =====
    proc = ProcessConditions(temp_C=args.temp, rate_C_min=args.rate, time_hr=args.time)
    r = pred.predict(feed, proc)
    
    if args.json:
        output({
            'feedstock': {'sulfur': args.sulfur, 'oxygen': args.oxygen, 'aromatics': args.aromatics, 'mcr': args.mcr},
            'process': {'temp_C': args.temp, 'rate_C_min': args.rate, 'time_hr': args.time},
            'result': {
                'd002_nm': r.d002_nm, 'in_goldilocks': r.in_goldilocks,
                'capacity_mAh_g': r.capacity_mAh_g, 'ice_pct': r.ice_pct,
                'bet_m2_g': r.bet_m2_g, 'yield_pct': r.yield_pct,
                'quality_score': r.quality_score, 'grade': r.grade
            }
        })
    else:
        print(f"\n{'='*55}")
        print("FCC HARD CARBON OPTIMIZER")
        print(f"{'='*55}")
        print(f"Feed: S={feed.sulfur_wt_pct}% | Proc: T={proc.temp_C}°C")
        print(f"\nd002: {r.d002_nm:.4f}nm {'✅ GOLDILOCKS' if r.in_goldilocks else '❌ OUTSIDE'}")
        print(f"Capacity: {r.capacity_mAh_g:.0f} mAh/g | ICE: {r.ice_pct:.1f}%")
        print(f"Score: {r.quality_score}/100 | Grade: {r.grade}")
        print(f"{'='*55}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
