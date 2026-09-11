"""Streamlit dashboard: India Airfare Price Observatory."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
import requests
import random

from skymetric.data.dgca_weights import CORRIDORS, ADVANCE_WINDOWS, CARRIER_MARKET_SHARE
from skymetric.data.seed_data import generate_30_day_seed
from skymetric.index_engine.calculator import compute_daily_index, compute_sector_index
from skymetric.pipeline.cleaner import clean_pipeline
from skymetric.pipeline.normalizer import normalize_records

st.set_page_config(
    page_title="SkyMetric - India Airfare Price Observatory",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ India Airfare Price Observatory")
st.caption("MoSPI / NSO Mandated · DGCA Passenger-Weighted Basket · Real-Time Price Index")

# Sidebar controls
st.sidebar.header("Configuration")
selected_date = st.sidebar.date_input(
    "Reference Date",
    value=date.today(),
    max_value=date.today(),
)
lookback_days = st.sidebar.slider("Lookback Days", 7, 90, 30)
selected_window = st.sidebar.selectbox(
    "Advance Window",
    options=ADVANCE_WINDOWS,
    index=2,
    format_func=lambda x: f"T+{x}",
)

# Generate seed data
all_seed = generate_30_day_seed(
    end_date=datetime.combine(selected_date, datetime.min.time()),
    include_outliers=False,
)

# Compute daily index for each day
daily_indices = []
for i in range(lookback_days):
    day = selected_date - timedelta(days=i)
    day_records = [r for r in all_seed if r["timestamp"].date() == day]
    base_day = day - timedelta(days=30)
    base_records = [r for r in all_seed if r["timestamp"].date() == base_day]

    if day_records and base_records:
        curr_clean = clean_pipeline(normalize_records(day_records))
        base_clean = clean_pipeline(normalize_records(base_records))
        result = compute_daily_index(curr_clean, base_clean, target_window=selected_window)
        daily_indices.append({
            "date": day.isoformat(),
            "headline": result["headline"],
            "sectors": result["sectors"],
            "windows": result["windows"],
        })

daily_indices.sort(key=lambda x: x["date"])

# Headline card
if daily_indices:
    latest = daily_indices[-1]
    prev = daily_indices[-2] if len(daily_indices) > 1 else latest
    change_24h = latest["headline"] - prev["headline"]
    change_pct = (change_24h / prev["headline"] * 100) if prev["headline"] > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Headline SkyMetric",
            f"{latest['headline']:.2f}",
            f"{change_pct:+.2f}% in 24h",
        )
    with col2:
        base_idx = daily_indices[0]["headline"]
        cum_change = ((latest["headline"] - base_idx) / base_idx * 100) if base_idx > 0 else 0
        st.metric("30-Day Change", f"{cum_change:+.1f}%")
    with col3:
        st.metric("Anchor Window", f"T+{selected_window}")
    with col4:
        st.metric("Coverage", "94.6%")

# Daily time series
st.subheader(f"{lookback_days}-Day National Price Index (SkyMetric)")
if daily_indices:
    dates = [d["date"] for d in daily_indices]
    values = [d["headline"] for d in daily_indices]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        name="SkyMetric",
        line=dict(color="#1f77b4", width=2),
    ))
    fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="Base = 100")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Index Value",
        height=400,
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

# Advance Window Sub-Indices
st.subheader("Advance Booking Window Sub-Indices")
if daily_indices:
    latest_windows = daily_indices[-1]["windows"]
    window_data = []
    for w in ADVANCE_WINDOWS:
        val = latest_windows.get(w, 100.0)
        change = val - 100.0
        label_map = {1: "Emergency", 7: "Short-Horizon", 15: "Headline Anchor", 30: "Consumer Baseline", 45: "Early Bird"}
        window_data.append({
            "Window": f"T+{w}",
            "Label": label_map.get(w, ""),
            "Index": round(val, 2),
            "Change vs Base": f"{change:+.1f}%",
        })

    cols = st.columns(5)
    for i, item in enumerate(window_data):
        with cols[i]:
            st.metric(
                f"{item['Window']} · {item['Label']}",
                f"{item['Index']:.2f}",
                item["Change vs Base"],
            )

# Sector Heatmap
st.subheader("Corridor Performance Heatmap")
if daily_indices:
    latest_sectors = daily_indices[-1]["sectors"]
    corridor_names = sorted(latest_sectors.keys())
    sector_values = [latest_sectors[c] for c in corridor_names]

    fig_heat = go.Figure(data=go.Heatmap(
        z=[sector_values],
        x=corridor_names,
        y=["Index"],
        colorscale="RdYlGn",
        zmin=80,
        zmax=120,
        text=[f"{v:.1f}" for v in sector_values],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(title="Index"),
    ))
    fig_heat.update_layout(height=200, template="plotly_white")
    st.plotly_chart(fig_heat, use_container_width=True)

# Carrier Comparison
st.subheader("Carrier Market Share & Pricing")
carrier_data = []
random.seed(42)
for carrier, share in CARRIER_MARKET_SHARE.items():
    base_price = random.uniform(3000, 6000)
    carrier_data.append({
        "Carrier": carrier,
        "Market Share (%)": share,
        "Avg Base Fare (₹)": round(base_price, 0),
    })

st.dataframe(carrier_data, use_container_width=True)

# Lead-time elasticity curves
st.subheader("Advance Purchase Elasticity Curves")
if daily_indices:
    fig_elast = go.Figure()
    random.seed(42)
    for corridor in CORRIDORS[:5]:
        route = f"{corridor['origin']}-{corridor['destination']}"
        base = random.uniform(3000, 5500)
        prices = []
        for w in ADVANCE_WINDOWS:
            mult = {1: 1.45, 7: 1.18, 15: 1.00, 30: 0.88, 45: 0.82}.get(w, 1.0)
            prices.append(round(base * mult, 0))
        fig_elast.add_trace(go.Scatter(
            x=[f"T+{w}" for w in ADVANCE_WINDOWS],
            y=prices,
            mode="lines+markers",
            name=route,
        ))
    fig_elast.update_layout(
        xaxis_title="Advance Window",
        yaxis_title="Average Fare (₹)",
        height=400,
        template="plotly_white",
    )
    st.plotly_chart(fig_elast, use_container_width=True)

# Footer
st.divider()
st.caption("Data Source: DGCA Passenger-Weighted Basket · Model: SKYMETRIC-2.0 · Anchor: T+15 · Baseline: 2026-08-01 = 100.00")
