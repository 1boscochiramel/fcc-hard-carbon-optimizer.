"""FCC Hard Carbon Optimizer - Streamlit Dashboard"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fcc_hard_carbon import (
    Feedstock, ProcessConditions, HardCarbonPredictor, GoldilocksAnalyzer,
    ProcessOptimizer, SensitivityAnalyzer, generate_contour_data,
    EconomicsCalculator
)

st.set_page_config(page_title="FCC Hard Carbon Optimizer", page_icon="🔋", layout="wide")

# ===== SIDEBAR =====
st.sidebar.title("🔋 FCC Hard Carbon")
st.sidebar.markdown("**Na-ion Battery Anode Optimizer**")

st.sidebar.header("📊 Feedstock")
sulfur = st.sidebar.slider("Sulfur (wt%)", 1.0, 6.0, 3.5, 0.1)
oxygen = st.sidebar.slider("Oxygen (wt%)", 0.5, 3.0, 1.0, 0.1)
aromatics = st.sidebar.slider("Aromatics (%)", 70.0, 95.0, 85.0, 1.0)
mcr = st.sidebar.slider("MCR (wt%)", 15.0, 35.0, 22.0, 1.0)

st.sidebar.header("⚙️ Process")
temp = st.sidebar.slider("Temperature (°C)", 900, 1300, 1100, 10)
rate = st.sidebar.slider("Heating Rate (°C/min)", 1.0, 20.0, 5.0, 0.5)
hold_time = st.sidebar.slider("Hold Time (hr)", 0.5, 4.0, 2.0, 0.25)

st.sidebar.header("💰 Economics")
fcc_tpy = st.sidebar.number_input("FCC Oil (TPY)", 1000, 50000, 10000, 1000)
yield_pct = st.sidebar.slider("Char Yield (%)", 25, 45, 35, 1)

# Create objects
feed = Feedstock(sulfur_wt_pct=sulfur, oxygen_wt_pct=oxygen, aromatics_pct=aromatics, mcr_wt_pct=mcr)
proc = ProcessConditions(temp_C=temp, rate_C_min=rate, time_hr=hold_time)
predictor = HardCarbonPredictor()
analyzer = GoldilocksAnalyzer()

# ===== MAIN CONTENT =====
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Predict", "🔍 Optimize", "📊 Sensitivity", "🗺️ Contours", "💰 Economics"])

# ===== TAB 1: PREDICT =====
with tab1:
    st.header("Property Prediction")
    
    result = predictor.predict(feed, proc)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("d002 Interlayer", f"{result.d002_nm:.4f} nm", 
                  "IN GOLDILOCKS ✅" if result.in_goldilocks else "OUTSIDE ❌")
        st.metric("Capacity", f"{result.capacity_mAh_g:.0f} mAh/g")
    
    with col2:
        st.metric("ICE", f"{result.ice_pct:.1f}%")
        st.metric("BET Surface", f"{result.bet_m2_g:.1f} m²/g")
    
    with col3:
        st.metric("Yield", f"{result.yield_pct:.1f}%")
        st.metric("Quality Score", f"{result.quality_score:.0f}/100", result.grade)
    
    # Goldilocks gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=result.d002_nm,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "d002 Interlayer Spacing (nm)"},
        delta={'reference': 0.385},
        gauge={
            'axis': {'range': [0.34, 0.42]},
            'bar': {'color': "green" if result.in_goldilocks else "red"},
            'steps': [
                {'range': [0.34, 0.37], 'color': "lightgray"},
                {'range': [0.37, 0.40], 'color': "lightgreen"},
                {'range': [0.40, 0.42], 'color': "lightgray"}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 0.385}
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Diagnostics
    st.subheader("💡 Diagnostics")
    for diag in analyzer.diagnose(result):
        st.write(diag)

# ===== TAB 2: OPTIMIZE =====
with tab2:
    st.header("Latin Hypercube Optimization")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        n_samples = st.selectbox("Samples", [200, 500, 1000, 2000], index=1)
        top_n = st.selectbox("Top N", [5, 10, 20], index=1)
        run_opt = st.button("🚀 Run Optimization", type="primary")
    
    if run_opt:
        with st.spinner(f"Sampling {n_samples} conditions..."):
            opt = ProcessOptimizer(feed)
            top_results = opt.optimize(n_samples, top_n)
            stats = opt.get_stats()
        
        st.success(f"Found {stats['goldilocks']}/{stats['total']} in Goldilocks ({stats['rate_pct']:.1f}%)")
        
        if top_results:
            st.subheader(f"🏆 Top {len(top_results)} Conditions")
            
            df = pd.DataFrame([{
                'Rank': i+1, 'Temp (°C)': r.temp_C, 'Rate (°C/min)': r.rate_C_min,
                'Time (hr)': r.time_hr, 'd002 (nm)': r.d002_nm, 'Capacity': r.capacity,
                'ICE (%)': r.ice_pct, 'Score': r.score
            } for i, r in enumerate(top_results)])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "top_conditions.csv", "text/csv")

# ===== TAB 3: SENSITIVITY =====
with tab3:
    st.header("Sensitivity Analysis")
    
    sens = SensitivityAnalyzer(feed, proc)
    results = sens.analyze()
    
    st.info(f"Base case: d002 = {sens.base_d002:.4f} nm")
    
    params = [r['param'] for r in results]
    lows = [r['low'] * 1000 for r in results]
    highs = [r['high'] * 1000 for r in results]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(y=params, x=lows, orientation='h', name='-20%', marker_color='steelblue'))
    fig.add_trace(go.Bar(y=params, x=highs, orientation='h', name='+20%', marker_color='firebrick'))
    fig.add_vline(x=0, line_dash="dash", line_color="black")
    fig.update_layout(title="Parameter Sensitivity (Δd002 in mÅ)", barmode='overlay', height=350,
                      xaxis_title="Change in d002 (mÅ)")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🔑 Key Insight")
    st.write(f"**{results[0]['param']}** has the largest impact on d002 (±{results[0]['impact']*1000:.1f} mÅ)")

# ===== TAB 4: CONTOURS =====
with tab4:
    st.header("Process Maps")
    
    with st.spinner("Generating contour data..."):
        data = generate_contour_data(feed, n=25)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Contour(x=data['temps'], y=data['sulfurs'], z=data['d002'],
                                   colorscale='Viridis', contours=dict(showlabels=True),
                                   colorbar=dict(title='d002 (nm)')))
        fig1.add_trace(go.Contour(x=data['temps'], y=data['sulfurs'], z=data['d002'],
                                   contours=dict(start=0.37, end=0.37, size=0.001, coloring='lines'),
                                   line=dict(color='lime', width=3), showscale=False))
        fig1.add_trace(go.Contour(x=data['temps'], y=data['sulfurs'], z=data['d002'],
                                   contours=dict(start=0.40, end=0.40, size=0.001, coloring='lines'),
                                   line=dict(color='red', width=3), showscale=False))
        fig1.update_layout(title="d002 Interlayer Spacing", xaxis_title="Temperature (°C)",
                           yaxis_title="Sulfur (%)", height=450)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Contour(x=data['temps'], y=data['sulfurs'], z=data['capacity'],
                                   colorscale='RdYlGn', contours=dict(showlabels=True),
                                   colorbar=dict(title='mAh/g')))
        fig2.update_layout(title="Reversible Capacity", xaxis_title="Temperature (°C)",
                           yaxis_title="Sulfur (%)", height=450)
        st.plotly_chart(fig2, use_container_width=True)

# ===== TAB 5: ECONOMICS =====
with tab5:
    st.header("Business Case Analysis")
    
    econ = EconomicsCalculator(fcc_tpy, yield_pct)
    capex = econ.get_capex()
    opex = econ.get_opex()
    rev = econ.get_revenue()
    fin = econ.get_npv_irr()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NPV", f"₹{fin['npv_cr']:.0f} Cr", f"IRR: {fin['irr_pct']:.0f}%")
    col2.metric("CAPEX", f"₹{capex['total_cr']:.0f} Cr")
    col3.metric("EBITDA", f"₹{fin['ebitda_cr']:.0f} Cr/yr")
    col4.metric("Payback", f"{fin['payback_yr']} years")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Scale")
        st.write(f"- FCC Oil Input: **{fcc_tpy:,} TPY**")
        st.write(f"- Hard Carbon Output: **{rev['hc_tpy']:,.0f} TPY**")
        st.write(f"- Cost: **₹{opex['cost_per_kg']:.1f}/kg** | Price: **₹{rev['price_per_kg']:.0f}/kg**")
    
    with col2:
        st.subheader("📊 Price Sensitivity")
        scenarios = econ.scenarios()
        df_scen = pd.DataFrame(scenarios)
        df_scen.columns = ['Change', '₹/kg', 'NPV (Cr)', 'IRR (%)', 'Payback']
        st.dataframe(df_scen, use_container_width=True, hide_index=True)

# ===== FOOTER =====
st.sidebar.divider()
st.sidebar.caption("FCC Hard Carbon Optimizer v1.0")
st.sidebar.caption("Goldilocks: d002 = 0.37-0.40 nm")
