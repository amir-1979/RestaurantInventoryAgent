import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Restaurant Inventory Dashboard",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .expired-card {
        border-left-color: #ff6b6b;
    }
    .warning-card {
        border-left-color: #ffa726;
    }
    .fresh-card {
        border-left-color: #66bb6a;
    }
</style>
""", unsafe_allow_html=True)

def load_inventory_simple(csv_path: str):
    """Load CSV and detect expiration column"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV is empty: {csv_path}")

    # detect expiration column
    possible_cols = ["expiration_date", "expiry_date", "expires", "best_before"]
    date_col = next((c for c in df.columns if c.lower() in possible_cols), None)
    if not date_col:
        raise ValueError(
            f"Could not find an expiration date column in {csv_path}. "
            f"Add one named one of: {possible_cols}"
        )

    # normalize date column
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if df[date_col].isna().any():
        bad = df[df[date_col].isna()]
        raise ValueError(
            "Some expiration dates failed to parse. Ensure ISO dates (YYYY-MM-DD) or clean formats.\n"
            f"Bad rows (showing up to 5):\n{bad.head(5)}"
        )
    return df, date_col

def slice_inventory_simple(df: pd.DataFrame, date_col: str):
    """Return expired, expiring (<=7 days), and fresh slices"""
    today = pd.Timestamp(datetime.now().date())
    soon = today + pd.Timedelta(days=7)

    expired = df[df[date_col] < today].copy()
    expiring_7d = df[(df[date_col] >= today) & (df[date_col] <= soon)].copy()
    fresh = df[df[date_col] > soon].copy()
    return expired, expiring_7d, fresh

@st.cache_data
def load_and_analyze_inventory():
    """Load inventory data and perform analysis"""
    try:
        df, date_col = load_inventory_simple("inventory.csv")
        expired, expiring_7d, fresh = slice_inventory_simple(df, date_col)
        return df, expired, expiring_7d, fresh, date_col
    except Exception as e:
        st.error(f"Error loading inventory: {str(e)}")
        return None, None, None, None, None

def create_expiration_chart(df, date_col):
    """Create a timeline chart showing expiration dates"""
    today = datetime.now().date()
    df_copy = df.copy()
    
    # Calculate days until expiry safely
    def calc_days(date_val):
        try:
            if pd.isna(date_val):
                return 0
            date_only = date_val.date() if hasattr(date_val, 'date') else date_val
            return (date_only - today).days
        except:
            return 0
    
    df_copy['days_until_expiry'] = df_copy[date_col].apply(calc_days)
    
    # Categorize items
    df_copy['status'] = df_copy['days_until_expiry'].apply(
        lambda x: 'Expired' if x < 0 else 'Expiring Soon' if x <= 7 else 'Fresh'
    )
    
    color_map = {'Expired': '#ff6b6b', 'Expiring Soon': '#ffa726', 'Fresh': '#66bb6a'}
    
    fig = px.scatter(
        df_copy, 
        x='days_until_expiry', 
        y='item',
        color='status',
        size='quantity',
        hover_data=['category', 'expiration_date'],
        color_discrete_map=color_map,
        title="Inventory Expiration Timeline"
    )
    
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Today")
    fig.add_vline(x=7, line_dash="dash", line_color="orange", annotation_text="7 Days")
    
    fig.update_layout(
        xaxis_title="Days Until Expiry",
        yaxis_title="Items",
        height=600
    )
    
    return fig

def create_category_chart(expired, expiring_7d, fresh):
    """Create a category breakdown chart"""
    categories = {}
    
    for df, status in [(expired, 'Expired'), (expiring_7d, 'Expiring Soon'), (fresh, 'Fresh')]:
        if not df.empty:
            cat_counts = df['category'].value_counts()
            for cat, count in cat_counts.items():
                if cat not in categories:
                    categories[cat] = {'Expired': 0, 'Expiring Soon': 0, 'Fresh': 0}
                categories[cat][status] = count
    
    if categories:
        df_cat = pd.DataFrame(categories).T.fillna(0)
        
        fig = go.Figure()
        colors = {'Expired': '#ff6b6b', 'Expiring Soon': '#ffa726', 'Fresh': '#66bb6a'}
        
        for status in ['Expired', 'Expiring Soon', 'Fresh']:
            if status in df_cat.columns:
                fig.add_trace(go.Bar(
                    name=status,
                    x=df_cat.index,
                    y=df_cat[status],
                    marker_color=colors[status]
                ))
        
        fig.update_layout(
            title="Items by Category and Status",
            xaxis_title="Category",
            yaxis_title="Number of Items",
            barmode='stack'
        )
        
        return fig
    return None

def main():
    st.title("🍽️ Restaurant Inventory Dashboard")
    st.markdown("Real-time inventory analysis and expiration tracking")
    
    # Sidebar
    st.sidebar.header("Dashboard Controls")
    
    # Load data
    df, expired, expiring_7d, fresh, date_col = load_and_analyze_inventory()
    
    if df is None:
        st.error("Failed to load inventory data. Please check your CSV file.")
        return
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        # Try different rerun methods based on Streamlit version
        try:
            st.rerun()
        except AttributeError:
            try:
                st.experimental_rerun()
            except AttributeError:
                st.info("Please refresh the page manually to see updated data.")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Items",
            value=len(df),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Expired Items",
            value=len(expired),
            delta=f"-{len(expired)} items" if len(expired) > 0 else "0 items",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Expiring Soon (≤7 days)",
            value=len(expiring_7d),
            delta=f"⚠️ {len(expiring_7d)} items" if len(expiring_7d) > 0 else "0 items",
            delta_color="off"
        )
    
    with col4:
        st.metric(
            label="Fresh Items",
            value=len(fresh),
            delta=f"✅ {len(fresh)} items"
        )
    
    # Charts section
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Expiration timeline chart
        timeline_fig = create_expiration_chart(df, date_col)
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    with col2:
        # Category breakdown chart
        category_fig = create_category_chart(expired, expiring_7d, fresh)
        if category_fig:
            st.plotly_chart(category_fig, use_container_width=True)
    
    # Data tables section
    st.markdown("---")
    st.header("📊 Detailed Inventory Data")
    
    # Tabs for different data views
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Expired", "⚠️ Expiring Soon", "✅ Fresh", "📋 All Items"])
    
    with tab1:
        st.subheader("Expired Items")
        if not expired.empty:
            st.dataframe(
                expired.sort_values(date_col),
                use_container_width=True
            )
            
            # Download button for expired items
            csv = expired.to_csv(index=False)
            st.download_button(
                label="📥 Download Expired Items CSV",
                data=csv,
                file_name=f"expired_items_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.success("No expired items! 🎉")
    
    with tab2:
        st.subheader("Items Expiring Within 7 Days")
        if not expiring_7d.empty:
            st.dataframe(
                expiring_7d.sort_values(date_col),
                use_container_width=True
            )
            
            # Download button for expiring items
            csv = expiring_7d.to_csv(index=False)
            st.download_button(
                label="📥 Download Expiring Items CSV",
                data=csv,
                file_name=f"expiring_items_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.success("No items expiring soon! 🎉")
    
    with tab3:
        st.subheader("Fresh Items (>7 days shelf life)")
        if not fresh.empty:
            st.dataframe(
                fresh.sort_values(date_col),
                use_container_width=True
            )
        else:
            st.warning("No fresh items found.")
    
    with tab4:
        st.subheader("Complete Inventory")
        st.dataframe(
            df.sort_values(date_col),
            use_container_width=True
        )
        
        # Download button for complete inventory
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Complete Inventory CSV",
            data=csv,
            file_name=f"complete_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Basic recommendations section
    st.markdown("---")
    st.header("📋 Smart Recommendations")
    
    if st.button("📋 Generate Recommendations", type="primary"):
        st.markdown("### 📋 Inventory Action Plan")
        
        recommendations = []
        
        if not expired.empty:
            recommendations.append("🚨 **Immediate Actions for Expired Items:**")
            for _, item in expired.iterrows():
                recommendations.append(f"   • Remove {item['item']} (expired {item[date_col].strftime('%Y-%m-%d')})")
            recommendations.append("")
        
        if not expiring_7d.empty:
            recommendations.append("⚠️ **Items Expiring Soon (Action Required):**")
            for _, item in expiring_7d.iterrows():
                days_left = (item[date_col].date() - datetime.now().date()).days
                recommendations.append(f"   • {item['item']}: {days_left} days left - Consider discount/special menu")
            recommendations.append("")
        
        # Category-based recommendations
        if not expired.empty or not expiring_7d.empty:
            urgent_items = pd.concat([expired, expiring_7d])
            categories = urgent_items['category'].value_counts()
            
            recommendations.append("📊 **Category Analysis:**")
            for category, count in categories.items():
                recommendations.append(f"   • {category}: {count} items need attention")
            recommendations.append("")
        
        recommendations.append("💡 **General Recommendations:**")
        recommendations.append("   • Implement FIFO (First In, First Out) rotation")
        recommendations.append("   • Check storage temperatures and conditions")
        recommendations.append("   • Consider smaller, more frequent orders for perishables")
        recommendations.append("   • Create daily specials using items expiring soon")
        
        for rec in recommendations:
            st.markdown(rec)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}* | "
        f"*Data source: inventory.csv*"
    )

if __name__ == "__main__":
    main()