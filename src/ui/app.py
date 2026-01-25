"""Streamlit UI for Apriori Ad Portfolio Simulator."""

import sys
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List
import json

from src.utils.schemas import PortfolioRecommendation, AdPerformance

# Set page config must be called first, before any other Streamlit commands
st.set_page_config(
    page_title="Apriori - Ad Portfolio Simulator",
    page_icon="🎯",
    layout="wide"
)


def render_header():
    """Render app header."""
    st.title("🎯 Apriori Ad-Portfolio Simulator")
    st.markdown("""
    **Pre-Flight Simulator for Ad Spend** | Mathematically solve for optimal creative portfolio before spending a single dollar.
    """)
    st.divider()


def render_portfolio_cards(recommendations: List[PortfolioRecommendation]):
    """Display winning portfolio as cards."""
    st.subheader("🏆 Winning Portfolio")
    
    cols = st.columns(len(recommendations))
    
    for idx, rec in enumerate(recommendations):
        with cols[idx]:
            st.markdown(f"""
            <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 10px; color: white; text-align: center;'>
                <h2 style='margin: 0; font-size: 3em;'>{rec.budget_split}%</h2>
                <h3 style='margin: 10px 0;'>{rec.ad_id}</h3>
                <p style='font-style: italic; margin: 5px 0;'>{rec.role}</p>
                <hr style='border-color: rgba(255,255,255,0.3);'>
                <p style='margin: 5px 0;'><strong>Target:</strong> {rec.target_segment}</p>
                <p style='margin: 5px 0;'><strong>Reach:</strong> {rec.unique_reach} users</p>
                <p style='margin: 5px 0;'><strong>Expected Conversions:</strong> {rec.expected_conversions}</p>
            </div>
            """, unsafe_allow_html=True)


def render_heatmap(heatmap_data: dict):
    """Render performance heatmap."""
    st.subheader("🌡️ Audience Segment Performance Heatmap")
    
    rows = heatmap_data["rows"]
    cols = heatmap_data["cols"]
    matrix = heatmap_data["matrix"]
    
    # Create DataFrame for display
    df = pd.DataFrame(matrix, columns=cols, index=rows)
    
    st.dataframe(df, use_container_width=True)
    
    st.caption("""
    **Legend:** 🟢 Strong (30%+ conversion) | 🟡 Medium (15-30%) | 🟠 Weak (5-15%) | 🔴 Poor (<5%) | ⚪ No data
    """)


def render_performance_table(performances: dict):
    """Render detailed performance metrics table."""
    st.subheader("📊 Detailed Performance Metrics")
    
    # Convert to DataFrame
    data = []
    for ad_id, perf in performances.items():
        data.append({
            "Ad ID": ad_id,
            "Impressions": perf.total_impressions,
            "Clicks": perf.clicks,
            "Click Rate (%)": perf.click_rate,
            "High-Intent Leads": perf.high_intent_leads,
            "Conversion Rate (%)": perf.conversion_rate,
            "Unique Reach": perf.unique_reach
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values("Conversion Rate (%)", ascending=False)
    
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_overlap_chart(overlap_matrix: dict):
    """Render audience overlap visualization."""
    st.subheader("🔄 Audience Overlap Analysis")
    
    if not overlap_matrix:
        st.info("No overlap data available")
        return
    
    ad_ids = list(overlap_matrix.keys())
    
    # Build matrix for heatmap
    matrix_data = []
    for ad_a in ad_ids:
        row = []
        for ad_b in ad_ids:
            row.append(overlap_matrix[ad_a].get(ad_b, 0))
        matrix_data.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix_data,
        x=ad_ids,
        y=ad_ids,
        colorscale='RdYlGn_r',
        text=matrix_data,
        texttemplate='%{text:.0%}',
        textfont={"size": 12},
        colorbar=dict(title="Overlap %")
    ))
    
    fig.update_layout(
        title="Audience Overlap Between Ads",
        xaxis_title="Ad Creative",
        yaxis_title="Ad Creative",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("**Lower overlap = Better reach efficiency** | Diagonal = 100% (self-overlap)")


def render_alerts(alerts: List[str]):
    """Display wasted spend alerts."""
    if not alerts:
        st.success("✅ No wasted spend detected! All ads are performing efficiently.")
        return
    
    st.subheader("⚠️ Wasted Spend Alerts")
    
    for alert in alerts:
        st.warning(alert)


def render_budget_breakdown(recommendations: List[PortfolioRecommendation]):
    """Render budget allocation pie chart."""
    st.subheader("💰 Budget Allocation Breakdown")
    
    labels = [f"{rec.ad_id}\n({rec.role})" for rec in recommendations]
    values = [rec.budget_split for rec in recommendations]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=px.colors.qualitative.Bold)
    )])
    
    fig.update_layout(
        title="Recommended Budget Split",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_segment_distribution(segment_data: dict):
    """Render audience segment distribution per ad."""
    st.subheader("👥 Target Audience Distribution")
    
    if not segment_data:
        st.info("No segment data available")
        return
    
    # Prepare data for grouped bar chart
    all_segments = set()
    for ad_segments in segment_data.values():
        all_segments.update(ad_segments.keys())
    
    data = []
    for ad_id, segments in segment_data.items():
        for segment in all_segments:
            data.append({
                "Ad": ad_id,
                "Segment": segment,
                "Count": segments.get(segment, 0)
            })
    
    df = pd.DataFrame(data)
    
    fig = px.bar(
        df,
        x="Ad",
        y="Count",
        color="Segment",
        title="Engaged Users by Segment",
        barmode="group",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_validation_summary(validation_data: dict):
    """Render validation results."""
    with st.expander("🔍 Validation Summary (Anti-Hallucination Check)"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Reactions", validation_data.get("total", 0))
        
        with col2:
            st.metric("Valid", validation_data.get("valid", 0), 
                     delta_color="normal")
        
        with col3:
            flagged_pct = validation_data.get("flagged_percentage", 0)
            st.metric("Flagged", validation_data.get("flagged", 0), 
                     delta=f"{flagged_pct:.1f}%", delta_color="inverse")
        
        if validation_data.get("flagged", 0) > 0:
            st.caption("Some reactions were flagged for logical inconsistencies and excluded from analysis.")


def render_download_button(report_data: dict):
    """Provide JSON export of full report."""
    st.subheader("📥 Export Report")
    
    json_str = json.dumps(report_data, indent=2, default=str)
    
    st.download_button(
        label="Download Full Report (JSON)",
        data=json_str,
        file_name="apriori_report.json",
        mime="application/json"
    )


def render_dashboard(result: dict, validation_summary: dict = None):
    """Main dashboard renderer."""
    render_header()
    
    # Key metrics row
    st.header("📈 Strategic Verdict")
    
    recommendations = result.get("winning_portfolio", [])
    performances = result.get("all_performances", {})
    overlap_matrix = result.get("overlap_matrix", {})
    segments = result.get("audience_segments", {})
    alerts = result.get("wasted_spend_alerts", [])
    heatmap = result.get("visual_heatmap", {})
    
    # Portfolio cards
    if recommendations:
        render_portfolio_cards(recommendations)
    
    st.divider()
    
    # Alerts
    render_alerts(alerts)
    
    st.divider()
    
    # Budget breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        if recommendations:
            render_budget_breakdown(recommendations)
    
    with col2:
        if segments:
            render_segment_distribution(segments)
    
    st.divider()
    
    # Heatmap
    if heatmap:
        render_heatmap(heatmap)
    
    st.divider()
    
    # Performance table
    if performances:
        render_performance_table(performances)
    
    st.divider()
    
    # Overlap analysis
    if overlap_matrix:
        render_overlap_chart(overlap_matrix)
    
    st.divider()
    
    # Validation summary
    if validation_summary:
        render_validation_summary(validation_summary)
    
    st.divider()
    
    # Export
    render_download_button({
        "winning_portfolio": [rec.model_dump() for rec in recommendations] if recommendations else [],
        "all_performances": {k: v.model_dump() for k, v in performances.items()} if performances else {},
        "overlap_matrix": overlap_matrix,
        "audience_segments": segments,
        "wasted_spend_alerts": alerts,
        "visual_heatmap": heatmap
    })


def main():
    """Entry point for Streamlit app."""
    render_header()
    
    st.info("⚠️ This is a demo UI. Run the simulation via `main.py` to generate results.")
    
    # File uploader for pre-generated results
    st.subheader("Upload Simulation Results")
    uploaded_file = st.file_uploader("Upload JSON report", type=["json"])
    
    if uploaded_file:
        try:
            report_data = json.load(uploaded_file)
            
            # Parse back to proper objects
            recommendations = [
                PortfolioRecommendation(**rec) 
                for rec in report_data.get("winning_portfolio", [])
            ]
            
            performances = {
                k: AdPerformance(**v)
                for k, v in report_data.get("all_performances", {}).items()
            }
            
            result = {
                "winning_portfolio": recommendations,
                "all_performances": performances,
                "overlap_matrix": report_data.get("overlap_matrix", {}),
                "audience_segments": report_data.get("audience_segments", {}),
                "wasted_spend_alerts": report_data.get("wasted_spend_alerts", []),
                "visual_heatmap": report_data.get("visual_heatmap", {})
            }
            
            validation_summary = report_data.get("validation_summary")
            
            render_dashboard(result, validation_summary)
            
        except Exception as e:
            st.error(f"Error loading report: {str(e)}")


if __name__ == "__main__":
    main()
