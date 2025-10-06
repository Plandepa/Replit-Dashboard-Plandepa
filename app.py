import streamlit as st
import os
import base64
from auth import authenticate_user, check_permissions
from database import init_database
import importlib.util

# Page configuration
st.set_page_config(
    page_title="PLANDEPA Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Get PLANDEPA logo as base64
def get_logo_base64():
    try:
        with open("static/plandepa-logo.png", "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

# Initialize database
@st.cache_resource
def setup_database():
    init_database()
    return True

# Main application
def main():
    # Load CSS and setup database
    load_css()
    setup_database()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Authentication check
    if not st.session_state.authenticated:
        show_login()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header-new">
            <h1 class="plandepa-title">PLANDEPA</h1>
            <p class="plandepa-tagline">BUILD SMART, GROW SIMPLE</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Welcome, {st.session_state.username}**")
        st.markdown(f"*Role: {st.session_state.user_role.title() if st.session_state.user_role else 'Unknown'}*")
        
        st.markdown("---")
        
        # Modern Navigation Menu
        pages = {
            "📊 Dashboard": "dashboard",
            "👥 Customers": "customers",
            "📋 Estimates": "estimates", 
            "🔨 Jobs": "jobs",
            "🧾 Invoices": "invoices",
            "📁 Documents": "documents",
            "💰 Financials": "financials",
            "🤖 AI Caller": "ai_caller"
        }
        
        # Add admin page for super admin
        if st.session_state.user_role == "super_admin":
            pages["⚙️ Admin"] = "admin"
        
        # Initialize current page
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "📊 Dashboard"
        
        # Create modern navigation  
        for page_name in pages.keys():
            is_current = st.session_state.current_page == page_name
            button_label = f"🔹 {page_name}" if is_current else page_name
            
            if st.button(button_label, key=f"nav_{pages[page_name]}", 
                        use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()
        
        # Set selected page for compatibility - use the current page name
        selected_page = st.session_state.current_page
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.rerun()
    
    # Load selected page - convert display name to file name
    page_file_name = pages.get(selected_page, "dashboard")  # Default to dashboard if not found
    load_page(page_file_name)

def show_login():
    st.markdown("""
    <div class="login-container-new">
        <div class="login-form-wrapper">
            <div class="login-title">
                <h2>Welcome to PLANDEPA</h2>
                <p>Build Smart, Grow Simple</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
        <div class="login-card">
            <h3>Sign In</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            # Demo credentials info
            st.markdown("""
            <div class="demo-info">
                <small>Demo Login: <strong>admin</strong> / <strong>admin123</strong></small>
            </div>
            """, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if username and password:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user_role = user_data['role']
                        st.session_state.username = user_data['username']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")

def load_page(page_name):
    """Dynamically load page modules"""
    try:
        spec = importlib.util.spec_from_file_location(
            f"pages.{page_name}", 
            f"pages/{page_name}.py"
        )
        if spec is None or spec.loader is None:
            st.error(f"Could not load page specification for '{page_name}'")
            return
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Let each page handle its own permissions - remove double checking
        module.show()
    except FileNotFoundError:
        st.error(f"Page '{page_name}' not found.")
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")

if __name__ == "__main__":
    main()
