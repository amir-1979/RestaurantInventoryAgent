import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Try to import optional dependencies
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly not available. Charts will be disabled.")

# Page configuration
st.set_page_config(
    page_title="Restaurant Inventory Dashboard",
    page_icon="🍽️",
    layout="wide"
)

def safe_date_conversion(date_series):
    """Safely convert dates with multiple fallback methods"""
    try:
        # Try pandas to_datetime first
        converted = pd.to_datetime(date_series, errors='coerce')
        return converted
    except Exception:
        try:
            # Fallback to manual conversion
            def convert_single_date(date_str):
                try:
                    if pd.isna(date_str):
                        return pd.NaT
                    return pd.to_datetime(str(date_str))
                except:
                    return pd.NaT
            return date_series.apply(convert_single_date)
        except Exception:
            return pd.to_datetime(date_series, errors='coerce')

def load_inventory_ultra_safe(csv_path: str):
    """Ultra-safe CSV loading with comprehensive error handling"""
    try:
        if not os.path.exists(csv_path):
            st.error(f"❌ CSV file not found: {csv_path}")
            st.info("Please make sure inventory.csv is in the same directory as this script.")
            return None, None

        # Load CSV with error handling
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {e}")
            return None, None

        if df.empty:
            st.error("❌ CSV file is empty")
            return None, None

        # Find expiration date column
        possible_cols = ["expiration_date", "expiry_date", "expires", "best_before"]
        date_col = None
        
        for col in df.columns:
            if col.lower().strip() in [c.lower() for c in possible_cols]:
                date_col = col
                break
        
        if not date_col:
            st.error(f"❌ No expiration date column found. Expected one of: {possible_cols}")
            st.info(f"Available columns: {list(df.columns)}")
            return None, None

        # Convert dates safely
        original_count = len(df)
        df[date_col] = safe_date_conversion(df[date_col])
        
        # Remove rows with invalid dates
        df = df.dropna(subset=[date_col])
        
        if len(df) < original_count:
            st.warning(f"⚠️ Removed {original_count - len(df)} rows with invalid dates")
        
        if df.empty:
            st.error("❌ No valid dates found in the data")
            return None, None
            
        return df, date_col
        
    except Exception as e:
        st.error(f"❌ Unexpected error loading inventory: {e}")
        return None, None

def analyze_inventory_safe(df, date_col):
    """Safely analyze inventory with robust date handling"""
    try:
        today = pd.Timestamp(datetime.now().date())
        soon = today + pd.Timedelta(days=7)

        # Create boolean masks safely
        expired_mask = df[date_col] < today
        expiring_mask = (df[date_col] >= today) & (df[date_col] <= soon)
        fresh_mask = df[date_col] > soon

        expired = df[expired_mask].copy()
        expiring_7d = df[expiring_mask].copy()
        fresh = df[fresh_mask].copy()
        
        return expired, expiring_7d, fresh
        
    except Exception as e:
        st.error(f"❌ Error analyzing inventory: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_simple_chart(df, date_col):
    """Create a simple bar chart if plotly is not available"""
    try:
        if not PLOTLY_AVAILABLE:
            return None
            
        today = datetime.now().date()
        
        # Calculate status for each item
        statuses = []
        for _, row in df.iterrows():
            try:
                exp_date = row[date_col]
                if pd.isna(exp_date):
                    continue
                    
                exp_date_only = exp_date.date() if hasattr(exp_date, 'date') else exp_date
                days_diff = (exp_date_only - today).days
                
                if days_diff < 0:
                    statuses.append('Expired')
                elif days_diff <= 7:
                    statuses.append('Expiring Soon')
                else:
                    statuses.append('Fresh')
            except:
                statuses.append('Unknown')
        
        if not statuses:
            return None
            
        # Count statuses
        status_counts = pd.Series(statuses).value_counts()
        
        # Create simple bar chart
        fig = px.bar(
            x=status_counts.index,
            y=status_counts.values,
            title="Inventory Status Overview",
            color=status_counts.index,
            color_discrete_map={
                'Expired': '#ff6b6b',
                'Expiring Soon': '#ffa726', 
                'Fresh': '#66bb6a',
                'Unknown': '#cccccc'
            }
        )
        
        fig.update_layout(
            xaxis_title="Status",
            yaxis_title="Number of Items",
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Error creating chart: {e}")
        return None

def main():
    st.title("🍽️ Restaurant Inventory Dashboard")
    st.markdown("**Ultra-Safe** inventory analysis and expiration tracking")
    
    # Load data
    df, date_col = load_inventory_ultra_safe("inventory.csv")
    
    if df is None or date_col is None:
        st.stop()
    
    # Analyze inventory
    expired, expiring_7d, fresh = analyze_inventory_safe(df, date_col)
    
    # Display metrics
    st.markdown("### 📊 Inventory Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Items", len(df))
    
    with col2:
        st.metric("🚨 Expired", len(expired))
    
    with col3:
        st.metric("⚠️ Expiring Soon", len(expiring_7d))
    
    with col4:
        st.metric("✅ Fresh", len(fresh))
    
    # Chart section
    if PLOTLY_AVAILABLE:
        st.markdown("---")
        chart = create_simple_chart(df, date_col)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    # Data tables
    st.markdown("---")
    st.markdown("### 📋 Detailed Data")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Expired", "⚠️ Expiring Soon", "✅ Fresh", "📋 All Items"])
    
    with tab1:
        if not expired.empty:
            st.markdown(f"**{len(expired)} expired items:**")
            # Sort by expiration date (oldest first)
            try:
                expired_sorted = expired.sort_values(date_col)
                st.dataframe(expired_sorted)
                
                # Download button
                csv_data = expired_sorted.to_csv(index=False)
                st.download_button(
                    "📥 Download Expired Items",
                    csv_data,
                    f"expired_items_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Error displaying expired items: {e}")
                st.dataframe(expired)
        else:
            st.success("🎉 No expired items!")
    
    with tab2:
        if not expiring_7d.empty:
            st.markdown(f"**{len(expiring_7d)} items expiring within 7 days:**")
            try:
                expiring_sorted = expiring_7d.sort_values(date_col)
                st.dataframe(expiring_sorted)
                
                csv_data = expiring_sorted.to_csv(index=False)
                st.download_button(
                    "📥 Download Expiring Items",
                    csv_data,
                    f"expiring_items_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Error displaying expiring items: {e}")
                st.dataframe(expiring_7d)
        else:
            st.success("🎉 No items expiring soon!")
    
    with tab3:
        if not fresh.empty:
            st.markdown(f"**{len(fresh)} fresh items:**")
            try:
                fresh_sorted = fresh.sort_values(date_col)
                st.dataframe(fresh_sorted)
            except Exception as e:
                st.error(f"Error displaying fresh items: {e}")
                st.dataframe(fresh)
        else:
            st.warning("⚠️ No fresh items found")
    
    with tab4:
        st.markdown(f"**Complete inventory ({len(df)} items):**")
        try:
            df_sorted = df.sort_values(date_col)
            st.dataframe(df_sorted)
            
            csv_data = df_sorted.to_csv(index=False)
            st.download_button(
                "📥 Download Complete Inventory",
                csv_data,
                f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        except Exception as e:
            st.error(f"Error displaying complete inventory: {e}")
            st.dataframe(df)
    
    # Recommendations
    st.markdown("---")
    st.markdown("### 💡 Smart Recommendations")
    
    if st.button("📋 Generate Action Plan", type="primary"):
        st.markdown("#### 🎯 Recommended Actions")
        
        # Expired items actions
        if not expired.empty:
            st.markdown("**🚨 Immediate Actions (Expired Items):**")
            for idx, (_, item) in enumerate(expired.iterrows()):
                if idx >= 10:  # Limit to first 10 items
                    st.markdown(f"   ... and {len(expired) - 10} more expired items")
                    break
                try:
                    exp_date = item[date_col].strftime('%Y-%m-%d')
                    st.markdown(f"   • **Remove** {item.get('item', 'Unknown item')} (expired {exp_date})")
                except:
                    st.markdown(f"   • **Remove** {item.get('item', 'Unknown item')} (expired)")
            st.markdown("")
        
        # Expiring soon actions
        if not expiring_7d.empty:
            st.markdown("**⚠️ Priority Actions (Expiring Soon):**")
            for idx, (_, item) in enumerate(expiring_7d.iterrows()):
                if idx >= 10:  # Limit to first 10 items
                    st.markdown(f"   ... and {len(expiring_7d) - 10} more items expiring soon")
                    break
                try:
                    exp_date = item[date_col]
                    days_left = (exp_date.date() - datetime.now().date()).days
                    st.markdown(f"   • **{item.get('item', 'Unknown item')}**: {days_left} days left - Consider discount/special")
                except:
                    st.markdown(f"   • **{item.get('item', 'Unknown item')}**: Expiring soon - Consider discount/special")
            st.markdown("")
        
        # General recommendations
        st.markdown("**📋 General Best Practices:**")
        st.markdown("   • Implement FIFO (First In, First Out) rotation system")
        st.markdown("   • Check and maintain proper storage temperatures")
        st.markdown("   • Create daily specials featuring items expiring soon")
        st.markdown("   • Consider smaller, more frequent orders for highly perishable items")
        st.markdown("   • Review supplier delivery schedules and adjust orders accordingly")
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data source: inventory.csv")

if __name__ == "__main__":
    main()