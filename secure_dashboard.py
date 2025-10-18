import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import hashlib
import json

# Try to import optional dependencies
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Restaurant Inventory Dashboard - Login",
    page_icon="🔐",
    layout="wide"
)

# Default credentials (in production, store these securely)
DEFAULT_USERS = {
    "admin": "admin123",
    "manager": "manager123",
    "staff": "staff123"
}

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from file or use defaults"""
    users_file = "users.json"
    
    # Always ensure we have the default users available
    hashed_users = {username: hash_password(password) for username, password in DEFAULT_USERS.items()}
    
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                file_users = json.load(f)
                # Merge file users with defaults (file users take precedence)
                hashed_users.update(file_users)
                return hashed_users
        except Exception as e:
            st.warning(f"Error reading users file: {e}. Using defaults.")
    
    # Create/update default users file
    try:
        with open(users_file, 'w') as f:
            json.dump(hashed_users, f, indent=2)
        st.info("Created default users file with demo credentials.")
    except Exception as e:
        st.warning(f"Could not create users file: {e}. Using in-memory defaults.")
    
    return hashed_users

def verify_credentials(username, password):
    """Verify username and password"""
    users = load_users()
    
    # Debug info (remove in production)
    if username in users:
        input_hash = hash_password(password)
        stored_hash = users[username]
        return stored_hash == input_hash
    return False

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
                    if verify_credentials(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.login_time = datetime.now()
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
    
    # Show default credentials for demo
    st.markdown("---")
    with st.expander("🔍 Demo Credentials (for testing)"):
        st.markdown("**Default login credentials:**")
        for username, password in DEFAULT_USERS.items():
            st.markdown(f"• **{username}**: {password}")
        st.markdown("*In production, these would be securely managed.*")

def safe_date_conversion(date_series):
    """Safely convert dates with multiple fallback methods"""
    try:
        converted = pd.to_datetime(date_series, errors='coerce')
        return converted
    except Exception:
        try:
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

def load_inventory_secure(csv_path: str):
    """Secure inventory loading with comprehensive error handling"""
    try:
        if not os.path.exists(csv_path):
            st.error(f"❌ CSV file not found: {csv_path}")
            return None, None

        df = pd.read_csv(csv_path)
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
            return None, None

        # Convert dates safely
        original_count = len(df)
        df[date_col] = safe_date_conversion(df[date_col])
        df = df.dropna(subset=[date_col])
        
        if len(df) < original_count:
            st.warning(f"⚠️ Removed {original_count - len(df)} rows with invalid dates")
        
        if df.empty:
            st.error("❌ No valid dates found in the data")
            return None, None
            
        return df, date_col
        
    except Exception as e:
        st.error(f"❌ Error loading inventory: {e}")
        return None, None

def analyze_inventory_secure(df, date_col):
    """Securely analyze inventory"""
    try:
        today = pd.Timestamp(datetime.now().date())
        soon = today + pd.Timedelta(days=7)

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

def create_status_chart(df, date_col):
    """Create inventory status chart"""
    try:
        if not PLOTLY_AVAILABLE:
            return None
            
        today = datetime.now().date()
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
            
        status_counts = pd.Series(statuses).value_counts()
        
        # Create pie chart
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Inventory Status Distribution",
            color=status_counts.index,
            color_discrete_map={
                'Expired': '#ff6b6b',
                'Expiring Soon': '#ffa726', 
                'Fresh': '#66bb6a',
                'Unknown': '#cccccc'
            }
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Error creating chart: {e}")
        return None

def show_dashboard():
    """Display the main dashboard after login"""
    # Header with user info and logout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🍽️ Restaurant Inventory Dashboard")
        st.markdown(f"Welcome back, **{st.session_state.username}**!")
    
    with col2:
        st.markdown("### 👤 User Session")
        st.markdown(f"**User:** {st.session_state.username}")
        login_time = st.session_state.get('login_time', datetime.now())
        st.markdown(f"**Login:** {login_time.strftime('%H:%M')}")
        
        if st.button("🚪 Logout", type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Load and analyze data
    df, date_col = load_inventory_secure("inventory.csv")
    
    if df is None or date_col is None:
        st.stop()
    
    expired, expiring_7d, fresh = analyze_inventory_secure(df, date_col)
    
    # Metrics
    st.markdown("### 📊 Inventory Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Items", len(df))
    
    with col2:
        st.metric("🚨 Expired", len(expired), delta=f"-{len(expired)}" if len(expired) > 0 else "0")
    
    with col3:
        st.metric("⚠️ Expiring Soon", len(expiring_7d), delta=f"⚠️ {len(expiring_7d)}" if len(expiring_7d) > 0 else "0")
    
    with col4:
        st.metric("✅ Fresh", len(fresh), delta=f"✅ {len(fresh)}")
    
    # Chart
    if PLOTLY_AVAILABLE:
        st.markdown("---")
        chart = create_status_chart(df, date_col)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    # Data tables with role-based access
    st.markdown("---")
    st.markdown("### 📋 Inventory Details")
    
    # Different access levels based on user role
    if st.session_state.username == "admin":
        tabs = st.tabs(["🚨 Expired", "⚠️ Expiring Soon", "✅ Fresh", "📋 All Items", "👥 User Management"])
        show_user_management = True
    else:
        tabs = st.tabs(["🚨 Expired", "⚠️ Expiring Soon", "✅ Fresh", "📋 All Items"])
        show_user_management = False
    
    # Expired items tab
    with tabs[0]:
        if not expired.empty:
            st.markdown(f"**{len(expired)} expired items require immediate attention:**")
            try:
                expired_sorted = expired.sort_values(date_col)
                st.dataframe(expired_sorted, use_container_width=True)
                
                csv_data = expired_sorted.to_csv(index=False)
                st.download_button(
                    "📥 Download Expired Items Report",
                    csv_data,
                    f"expired_items_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Error displaying expired items: {e}")
        else:
            st.success("🎉 No expired items!")
    
    # Expiring soon tab
    with tabs[1]:
        if not expiring_7d.empty:
            st.markdown(f"**{len(expiring_7d)} items expiring within 7 days:**")
            try:
                expiring_sorted = expiring_7d.sort_values(date_col)
                st.dataframe(expiring_sorted, use_container_width=True)
                
                csv_data = expiring_sorted.to_csv(index=False)
                st.download_button(
                    "📥 Download Expiring Items Report",
                    csv_data,
                    f"expiring_items_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Error displaying expiring items: {e}")
        else:
            st.success("🎉 No items expiring soon!")
    
    # Fresh items tab
    with tabs[2]:
        if not fresh.empty:
            st.markdown(f"**{len(fresh)} fresh items:**")
            try:
                fresh_sorted = fresh.sort_values(date_col)
                st.dataframe(fresh_sorted, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying fresh items: {e}")
        else:
            st.warning("⚠️ No fresh items found")
    
    # All items tab
    with tabs[3]:
        st.markdown(f"**Complete inventory ({len(df)} items):**")
        try:
            df_sorted = df.sort_values(date_col)
            st.dataframe(df_sorted, use_container_width=True)
            
            csv_data = df_sorted.to_csv(index=False)
            st.download_button(
                "📥 Download Complete Inventory Report",
                csv_data,
                f"complete_inventory_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )
        except Exception as e:
            st.error(f"Error displaying complete inventory: {e}")
    
    # Admin-only user management tab
    if show_user_management:
        with tabs[4]:
            st.markdown("### 👥 User Management")
            st.markdown("*Admin-only section*")
            
            users = load_users()
            st.markdown("**Current Users:**")
            for username in users.keys():
                st.markdown(f"• {username}")
            
            st.markdown("**Add New User:**")
            with st.form("add_user_form"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                
                if st.form_submit_button("➕ Add User"):
                    if new_username and new_password:
                        users[new_username] = hash_password(new_password)
                        try:
                            with open("users.json", 'w') as f:
                                json.dump(users, f, indent=2)
                            st.success(f"✅ User '{new_username}' added successfully!")
                        except Exception as e:
                            st.error(f"❌ Error adding user: {e}")
                    else:
                        st.warning("⚠️ Please enter both username and password")
    
    # Action recommendations
    st.markdown("---")
    st.markdown("### 💡 Smart Recommendations")
    
    if st.button("📋 Generate Action Plan", type="primary"):
        st.markdown("#### 🎯 Recommended Actions")
        
        # Expired items actions
        if not expired.empty:
            st.markdown("**🚨 Immediate Actions (Expired Items):**")
            for idx, (_, item) in enumerate(expired.iterrows()):
                if idx >= 5:  # Limit to first 5 items
                    st.markdown(f"   ... and {len(expired) - 5} more expired items")
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
                if idx >= 5:  # Limit to first 5 items
                    st.markdown(f"   ... and {len(expiring_7d) - 5} more items expiring soon")
                    break
                try:
                    exp_date = item[date_col]
                    days_left = (exp_date.date() - datetime.now().date()).days
                    st.markdown(f"   • **{item.get('item', 'Unknown item')}**: {days_left} days left - Consider discount/special")
                except:
                    st.markdown(f"   • **{item.get('item', 'Unknown item')}**: Expiring soon - Consider discount/special")
            st.markdown("")
        
        # General recommendations
        st.markdown("**📋 Best Practices:**")
        st.markdown("   • Implement FIFO (First In, First Out) rotation")
        st.markdown("   • Monitor storage temperatures daily")
        st.markdown("   • Create specials for items expiring within 3 days")
        st.markdown("   • Review ordering patterns to reduce waste")
    
    # Footer with session info
    st.markdown("---")
    st.caption(f"Logged in as: {st.session_state.username} | Session started: {login_time.strftime('%Y-%m-%d %H:%M:%S')} | Data source: inventory.csv")

def main():
    """Main application logic"""
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Show appropriate page based on login status
    if st.session_state.logged_in:
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()