import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

# --------------------------
# CONFIGURATION
# --------------------------
st.set_page_config(
    page_title="💰 Financial Projection Dashboard",
    page_icon="📈",
    layout="wide"
)

# Dark mode styling
st.markdown("""
<style>
    /* Existing dark mode styles */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .css-1d391kg, .st-bh, .st-at, .st-ax { border-color: #2E3440; }
    .st-b8 { color: #FAFAFA; }
    .metric-label { font-size: 1.1rem; color: #88C0D0; }
    .metric-value { font-size: 1.5rem; font-weight: bold; color: #A3BE8C; }
    
    /* New sidebar text styling */
    [data-testid="stSidebar"] h2 {  /* Targets "Investment Parameters" and "Contributions" */
        color: #d94ea8 !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {  /* Targets CSV requirements text */
        color: #d94ea8 !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stSidebar"] strong {  /* Makes "CSV Format Requirements:" bold */
        color: #d94ea8 !important;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------
# DATA MODEL
# --------------------------
def calculate_projection(initial, contributions, start_date, daily_rate_percent):
    daily_rate = daily_rate_percent / 100  # Convert percentage to decimal
    dates = [start_date]
    balances = [initial]
    interests = [0]
    contribs = [0]
    
    current_balance = initial
    current_date = start_date
    
    # Sort contributions by date
    contributions = sorted(contributions, key=lambda x: x[0])
    
    for contrib_date, amount in contributions:
        while current_date < contrib_date:
            current_date += timedelta(days=1)
            daily_interest = current_balance * daily_rate
            current_balance += daily_interest
            dates.append(current_date)
            balances.append(round(current_balance, 2))
            interests.append(round(daily_interest, 2))
            contribs.append(0)
        
        current_balance += amount
        dates.append(contrib_date)
        balances.append(round(current_balance, 2))
        interests.append(0)
        contribs.append(amount)
    
    # Add remaining days if any
    while len(dates) < 366:  # Ensure 1 year projection
        current_date += timedelta(days=1)
        daily_interest = current_balance * daily_rate
        current_balance += daily_interest
        dates.append(current_date)
        balances.append(round(current_balance, 2))
        interests.append(round(daily_interest, 2))
        contribs.append(0)
    
    return pd.DataFrame({
        'Date': dates,
        'Balance': balances,
        'Interest': interests,
        'Contributions': contribs
    })

# --------------------------
# UI COMPONENTS
# --------------------------
def main():
    # Main header with logo
    # Main header with centered logo
    header = st.container()
    with header:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.image(
                "https://raw.githubusercontent.com/CryptoPlazaHQ/Stock/main/cryptoplaza_logo_white.png",
                width=300,
                use_container_width=True,  # Updated parameter
                output_format="PNG"
            )

    st.title("💰 Dynamic Financial Projection Dashboard")
    st.markdown("### Daily Compound Interest Calculator with Periodic Contributions")
    
    # Sidebar Controls
    with st.sidebar:
        st.header("Investment Parameters")
        initial = st.number_input("Initial Investment ($)", 
                                min_value=100, max_value=1000000, 
                                value=1000, step=100, format="%d")
        
        daily_rate_percent = st.number_input("Daily Interest Rate (%)", 
                                           min_value=0.01, max_value=100.0, 
                                           value=0.75, step=0.01, format="%.2f")
        
        start_date = st.date_input("Start Date", datetime.today())
        
        st.header("Contributions")
        contrib_freq = st.selectbox("Frequency", 
                                  ["Monthly", "Biweekly", "Weekly", "Custom"])
        
        if contrib_freq != "Custom":
            contrib_amount = st.number_input("Contribution Amount ($)", 
                                           min_value=0, max_value=10000, 
                                           value=100, step=25, format="%d")
            num_contribs = st.number_input("Number of Contributions", 
                                         min_value=1, max_value=360, 
                                         value=12, step=1, format="%d")
        
        st.markdown("""
        **CSV Format Requirements:**
        - Must contain columns: 'Date' and 'Amount'
        - Date format: YYYY-MM-DD
        - Amounts must be whole numbers
        """)
        contrib_csv = st.file_uploader("Upload Custom Contributions (CSV)", 
                                     type=["csv"])
    
    # Generate contributions
    contributions = []
    
    if contrib_freq == "Custom" and contrib_csv:
        try:
            df_csv = pd.read_csv(contrib_csv)
            df_csv['Date'] = pd.to_datetime(df_csv['Date']).dt.date
            contributions = [(row['Date'], int(row['Amount'])) 
                           for _, row in df_csv.iterrows()]
        except Exception as e:
            st.error(f"Error parsing CSV: {str(e)}")
    elif contrib_freq != "Custom":
        current_date = start_date
        for _ in range(num_contribs):
            if contrib_freq == "Monthly":
                current_date += relativedelta(months=+1)
            elif contrib_freq == "Biweekly":
                current_date += timedelta(weeks=2)
            elif contrib_freq == "Weekly":
                current_date += timedelta(weeks=1)
            
            contributions.append((current_date, contrib_amount))
    
    # Calculate projections
    df = calculate_projection(
        initial=initial,
        contributions=contributions,
        start_date=start_date,
        daily_rate_percent=daily_rate_percent
    )
    
    # --------------------------
    # METRICS & VISUALIZATIONS
    # --------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Balance", f"${df['Balance'].iloc[-1]:,.2f}")
    with col2:
        st.metric("Total Interest", f"${df['Interest'].sum():,.2f}")
    with col3:
        st.metric("Total Contributions", f"${df['Contributions'].sum():,.0f}")
    
    # Interactive Timeline
    fig = px.line(df, x='Date', y='Balance', 
                 title='Balance Growth Over Time',
                 template='plotly_dark')
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Composition Chart
    composition = pd.DataFrame({
        'Type': ['Initial', 'Contributions', 'Interest'],
        'Amount': [
            initial,
            df['Contributions'].sum(),
            df['Interest'].sum()
        ]
    })
    fig_pie = px.pie(composition, names='Type', values='Amount',
                    title='Balance Composition',
                    template='plotly_dark')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Detailed Data View
    with st.expander("View Detailed Transaction History"):
        st.dataframe(df.style.format({
            'Balance': '${:,.2f}',
            'Interest': '${:,.2f}',
            'Contributions': '${:.0f}'
        }), use_container_width=True)
    
    # Interest Analysis
    st.header("Interest Analysis")
    fig_interest = go.Figure()
    fig_interest.add_trace(go.Scatter(
        x=df['Date'], y=df['Interest'],
        name='Daily Interest',
        line=dict(color='#A3BE8C')
    ))
    fig_interest.update_layout(
        title='Daily Interest Earned',
        template='plotly_dark'
    )
    st.plotly_chart(fig_interest, use_container_width=True)

if __name__ == "__main__":
    main()
