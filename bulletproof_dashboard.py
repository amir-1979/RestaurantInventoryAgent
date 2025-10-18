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
    layout="wide"
)

def load_inventory_safe(csv_path: str):
    """Load CSV and detect expiration column - safe implementation"""
    try:
        if not os.path.exists(csv_path):
            st.error(f"CSV not found at: {csv_path}")
            return None, None

        df = pd.read_csv(csv_path)
        if df.empty:
            st.error(f"CSV is empty: {csv_path}")
            return None, None

        # detect expiration column
        possible_cols = ["expiration_date", "expiry_date", "expires", "best_before"]
        date_col = None
        for col in df.columns:
            if col.lower() in possible_cols:
                date_col = col
                break
        
        if not date_col:
            st.error(f"Could not find an expiration date column. Expected one of: {possible_cols}")
            return None, None

        # normalize date column
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            if df[date_col].isna().any():
                st.warning("Some expiration dates could not be parsed and will be ignored.")
                df = df.dropna(subset=[date_col])
        except Exception as e:
            st.error(f"Error parsing dates: {e}")
            return None, None
            
        return df, date_col
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        return None, None

def slice_inventory_safe(df: pd.DataFrame, date_col: str):
    """Return expired, expiring (<=7 days), and fresh slices - safe implementation"""
    try:
        today = pd.Timestamp(datetime.now().date())
        soon = today + pd.Timedelta(days=7)

        expired = df[df[date_col] < today].copy()
        expiring_7d = df[(df[date_col] >= today) & (df[date_col] <= soon)].copy()
        fresh = df[df[date_col] > soon].copy()
        return expired, expiring_7d, fresh
    except Exception as e:
        st.error(f"Error analyzing inventory: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_safe_chart(df, date_col):
    """Create a safe timeline chart"""
    try:
        if df.empty:
            return None
            
        today = datetime.now().date()
        df_copy = df.copy()
        df_copy['days_until_expiry'] = (df_copy[date_col].dt.date - today).dt.days
        
        # Categorize items
        def categorize_status(days):
            if days < 0:
                return 'Expired'
            elif days <= 7:
                return 'Expiring Soon'
            else:
                return 'Fresh'
        
        df_copy['status'] = df_copy['days_until_expiry'].apply(categorize_status)
        
        color_map = {'Expired': '#ff6b6b', 'Expiring Soon': '#ffa726', 'Fresh': '#66bb6a'}
        
        fig = px.scatter(
            df_copy, 
            x='days_until_expiry', 
            y='item',
            color='status',
            size='quantity',
            color_discrete_map=color_map,
            title="Inventory Expiration Timeline"
        )
        
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Today")
        fig.add_vline(x=7, line_dash="dash", line_color="orange", annotation_text="7 Days")
        
        fig.update_layout(
            xaxis_title="Days Until Expiry",
            yaxis_title="Items",
            height=500
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating chart: {e}")
        return None

def main():
    st.title("🍽️ Restaurant Inventory Dashboard")
    st.markdown("Real-time inventory analysis and expiration tracking")
    
    # Load data
    df, date_col = load_inventory_safe("inventory.csv")
    
    if df is None or date_col is None:
        st.stop()
    
    expired, expiring_7d, fresh = slice_inventory_safe(df, date_col)
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", len(df))
    
    with col2:
        st.metric("Expired Items", len(expired))
    
    with col3:
        st.metric("Expiring Soon (≤7 days)", len(expiring_7d))
    
    with col4:
        st.metric("Fresh Items", len(fresh))
    
    # Chart
    st.markdown("---")
    chart = create_safe_chart(df, date_col)
    if chart:
        st.plotly_chart(chart, use_container_width=True)
    
    # Data tables
    st.markdown("---")
    st.header("📊 Inventory Details")
    
    # Tabs for different data views
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Expired", "⚠️ Expiring Soon", "✅ Fresh", "📋 All Items"])
    
    with tab1:
        st.subheader("Expired Items")
        if not expired.empty:
            # Sort by expiration date
            expired_sorted = expired.sort_values(date_col)
            st.dataframe(expired_sorted)
            
            # Download button
            csv = expired_sorted.to_csv(index=False)
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
            expiring_sorted = expiring_7d.sort_values(date_col)
            st.dataframe(expiring_sorted)
            
            csv = expiring_sorted.to_csv(index=False)
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
            fresh_sorted = fresh.sort_values(date_col)
            st.dataframe(fresh_sorted)
        else:
            st.warning("No fresh items found.")
    
    with tab4:
        st.subheader("Complete Inventory")
        df_sorted = df.sort_values(date_col)
        st.dataframe(df_sorted)
        
        csv = df_sorted.to_csv(index=False)
        st.download_button(
            label="📥 Download Complete Inventory CSV",
            data=csv,
            file_name=f"complete_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Basic recommendations
    st.markdown("---")
    st.header("📋 Smart Recommendations")
    
    if st.button("📋 Generate Recommendations"):
        st.markdown("### 📋 Inventory Action Plan")
        
        if not expired.empty:
            st.markdown("🚨 **Immediate Actions for Expired Items:**")
            for _, item in expired.iterrows():
                exp_date = item[date_col].strftime('%Y-%m-%d')
                st.markdown(f"   • Remove **{item['item']}** (expired {exp_date})")
            st.markdown("")
        
        if not expiring_7d.empty:
            st.markdown("⚠️ **Items Expiring Soon (Action Required):**")
            for _, item in expiring_7d.iterrows():
                days_left = (item[date_col].date() - datetime.now().date()).days
                st.markdown(f"   • **{item['item']}**: {days_left} days left - Consider discount/special menu")
            st.markdown("")
        
        # Category analysis
        if not expired.empty or not expiring_7d.empty:
            urgent_items = pd.concat([expired, expiring_7d])
            if 'category' in urgent_items.columns:
                categories = urgent_items['category'].value_counts()
                
                st.markdown("📊 **Category Analysis:**")
                for category, count in categories.items():
                    st.markdown(f"   • **{category}**: {count} items need attention")
                st.markdown("")
        
        st.markdown("💡 **General Recommendations:**")
        st.markdown("   • Implement FIFO (First In, First Out) rotation")
        st.markdown("   • Check storage temperatures and conditions")
        st.markdown("   • Consider smaller, more frequent orders for perishables")
        st.markdown("   • Create daily specials using items expiring soon")
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()