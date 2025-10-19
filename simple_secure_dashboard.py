import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Try to import optional dependencies
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Secure Inventory Dashboard",
    page_icon="🔐",
    layout="wide"
)

# Simple in-memory user storage (for demo purposes)
VALID_USERS = {

}

def verify_login(username, password):
    """Simple login verification"""
    return username in VALID_USERS and VALID_USERS[username] == password

def show_login_page():
    """Display the login page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔐 Restaurant Inventory Dashboard</h1>
        <h3>Please login to access the inventory system</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 👤 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                login_button = st.form_submit_button("🔑 Login", use_container_width=True)
            
            if login_button:
                if username and password:
                    if verify_login(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.login_time = datetime.now()
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                        st.info("💡 Try: admin/XXX or manager/XXX or staff/XXX")
                else:
                    st.warning("⚠️ Please enter both username and password")
    
def load_inventory_data():
    """Load and process inventory data"""
    try:
        if not os.path.exists("inventory.csv"):
            st.error("❌ inventory.csv not found")
            return None, None, None, None, None

        df = pd.read_csv("inventory.csv")
        if df.empty:
            st.error("❌ Inventory file is empty")
            return None, None, None, None, None

        # Find date column
        date_col = None
        for col in df.columns:
            if 'expir' in col.lower() or 'date' in col.lower():
                date_col = col
                break
        
        if not date_col:
            st.error("❌ No expiration date column found")
            return None, None, None, None, None

        # Convert dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])

        # Analyze inventory
        today = pd.Timestamp(datetime.now().date())
        soon = today + pd.Timedelta(days=7)

        expired = df[df[date_col] < today].copy()
        expiring_7d = df[(df[date_col] >= today) & (df[date_col] <= soon)].copy()
        fresh = df[df[date_col] > soon].copy()

        return df, expired, expiring_7d, fresh, date_col

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None, None, None, None, None

def show_dashboard():
    """Display the main dashboard"""
    # Header with logout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🍽️ Restaurant Inventory Dashboard")
        st.markdown(f"Welcome, **{st.session_state.username}**!")
    
    with col2:
        st.markdown("### 👤 Session")
        st.markdown(f"**User:** {st.session_state.username}")
        if st.button("🚪 Logout"):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Load data
    df, expired, expiring_7d, fresh, date_col = load_inventory_data()
    
    if df is None:
        st.stop()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Items", len(df))
    
    with col2:
        st.metric("🚨 Expired", len(expired))
    
    with col3:
        st.metric("⚠️ Expiring Soon", len(expiring_7d))
    
    with col4:
        st.metric("✅ Fresh", len(fresh))
    
    # Simple chart
    if PLOTLY_AVAILABLE and not df.empty:
        st.markdown("---")
        
        # Create status data
        status_data = {
            'Status': ['Expired', 'Expiring Soon', 'Fresh'],
            'Count': [len(expired), len(expiring_7d), len(fresh)]
        }
        
        fig = px.bar(
            status_data,
            x='Status',
            y='Count',
            title="Inventory Status Overview",
            color='Status',
            color_discrete_map={
                'Expired': '#ff6b6b',
                'Expiring Soon': '#ffa726',
                'Fresh': '#66bb6a'
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Data tables
    st.markdown("---")
    st.header("📊 Inventory Details")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Expired", "⚠️ Expiring Soon", "✅ Fresh", "📋 All Items"])
    
    with tab1:
        if not expired.empty:
            st.markdown(f"**{len(expired)} expired items:**")
            st.dataframe(expired.sort_values(date_col))
            
            csv = expired.to_csv(index=False)
            st.download_button(
                "📥 Download Expired Items",
                csv,
                f"expired_items_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.success("🎉 No expired items!")
    
    with tab2:
        if not expiring_7d.empty:
            st.markdown(f"**{len(expiring_7d)} items expiring soon:**")
            st.dataframe(expiring_7d.sort_values(date_col))
            
            csv = expiring_7d.to_csv(index=False)
            st.download_button(
                "📥 Download Expiring Items",
                csv,
                f"expiring_items_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.success("🎉 No items expiring soon!")
    
    with tab3:
        if not fresh.empty:
            st.markdown(f"**{len(fresh)} fresh items:**")
            st.dataframe(fresh.sort_values(date_col))
        else:
            st.warning("⚠️ No fresh items")
    
    with tab4:
        st.markdown(f"**Complete inventory ({len(df)} items):**")
        st.dataframe(df.sort_values(date_col))
        
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Complete Inventory",
            csv,
            f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    
    # Recommendations
    st.markdown("---")
    st.header("💡 Recommendations")
    
    if st.button("📋 Generate Action Plan"):
        if not expired.empty:
            st.markdown("**🚨 Immediate Actions:**")
            for _, item in expired.head(5).iterrows():
                st.markdown(f"• Remove **{item.get('item', 'Unknown')}** (expired)")
        
        if not expiring_7d.empty:
            st.markdown("**⚠️ Priority Actions:**")
            for _, item in expiring_7d.head(5).iterrows():
                st.markdown(f"• **{item.get('item', 'Unknown')}** expiring soon - consider discount")
        
        st.markdown("**📋 General Tips:**")
        st.markdown("• Implement FIFO rotation")
        st.markdown("• Check storage conditions")
        st.markdown("• Create specials for expiring items")

def main():
    """Main application"""
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Show appropriate page
    if st.session_state.logged_in:
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()