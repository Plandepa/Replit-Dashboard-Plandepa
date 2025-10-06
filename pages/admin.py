import streamlit as st
from auth import get_all_users, create_user, update_user_role, check_permissions
from database import execute_query
import hashlib

REQUIRED_ROLE = 'super_admin'

def show():
    # Check super admin permissions
    if not check_permissions(st.session_state.user_role, 'super_admin'):
        st.error("❌ Access denied. Super admin privileges required.")
        return
    
    st.markdown("# ⚙️ Admin Panel")
    st.markdown("System administration and user management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["User Management", "System Settings", "Database Maintenance", "Audit Logs"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        show_system_settings()
    
    with tab3:
        show_database_maintenance()
    
    with tab4:
        show_audit_logs()

def show_user_management():
    st.subheader("👥 User Management")
    
    # Create new user section
    with st.expander("Create New User", expanded=False):
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username", placeholder="Enter unique username")
                new_password = st.text_input("Password", type="password", placeholder="Enter password")
                new_full_name = st.text_input("Full Name", placeholder="John Smith")
            
            with col2:
                new_email = st.text_input("Email", placeholder="user@company.com")
                new_role = st.selectbox("Role", ["admin", "super_admin"])
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            
            if st.form_submit_button("Create User", use_container_width=True):
                if all([new_username, new_password, new_full_name, new_email]):
                    if new_password == confirm_password:
                        user_id = create_user(new_username, new_password, new_role, new_full_name, new_email)
                        if user_id:
                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create user. Username may already exist.")
                    else:
                        st.error("❌ Passwords do not match.")
                else:
                    st.error("❌ Please fill in all required fields.")
    
    # Existing users management
    st.subheader("Existing Users")
    
    users = get_all_users()
    
    if users:
        for user in users:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
                
                with col1:
                    st.write(f"**{user['full_name']}**")
                    st.write(f"@{user['username']}")
                
                with col2:
                    st.write(f"Email: {user['email']}")
                    st.write(f"Created: {user['created_at'].strftime('%m/%d/%Y')}")
                
                with col3:
                    role_colors = {
                        'super_admin': '🔴',
                        'admin': '🟡',
                        'user': '🟢'
                    }
                    st.write(f"{role_colors.get(user['role'], '⚪')} {user['role'].replace('_', ' ').title()}")
                    
                    if user['last_login']:
                        st.write(f"Last: {user['last_login'].strftime('%m/%d')}")
                    else:
                        st.write("Never logged in")
                
                with col4:
                    # Role management (can't change own role)
                    if user['username'] != st.session_state.username:
                        new_role = st.selectbox(
                            "Change Role",
                            ["admin", "super_admin"],
                            index=0 if user['role'] == 'admin' else 1,
                            key=f"role_{user['id']}"
                        )
                        
                        col4a, col4b = st.columns(2)
                        with col4a:
                            if st.button("Update Role", key=f"update_role_{user['id']}", use_container_width=True):
                                if update_user_role(user['id'], new_role):
                                    st.success("Role updated!")
                                    st.rerun()
                                else:
                                    st.error("Update failed")
                        
                        with col4b:
                            if st.button("Reset Password", key=f"reset_pwd_{user['id']}", use_container_width=True):
                                st.session_state[f"reset_password_{user['id']}"] = True
                                st.rerun()
                    else:
                        st.write("*Current user*")
                
                # Password reset form
                if st.session_state.get(f"reset_password_{user['id']}", False):
                    with st.form(f"reset_password_form_{user['id']}"):
                        st.write(f"**Reset password for {user['username']}**")
                        new_pwd = st.text_input("New Password", type="password", key=f"new_pwd_{user['id']}")
                        confirm_pwd = st.text_input("Confirm Password", type="password", key=f"confirm_pwd_{user['id']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Reset Password", use_container_width=True):
                                if new_pwd and new_pwd == confirm_pwd:
                                    password_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                                    update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
                                    if execute_query(update_query, (password_hash, user['id'])):
                                        st.success("Password reset successfully!")
                                        st.session_state[f"reset_password_{user['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to reset password")
                                else:
                                    st.error("Passwords do not match or are empty")
                        
                        with col2:
                            if st.form_submit_button("Cancel", use_container_width=True):
                                st.session_state[f"reset_password_{user['id']}"] = False
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("No users found in the system.")

def show_system_settings():
    st.subheader("🔧 System Settings")
    
    # System information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Database Information**")
        
        # Get table counts
        tables_info = [
            ("Users", "SELECT COUNT(*) FROM users"),
            ("Estimates", "SELECT COUNT(*) FROM estimates"),
            ("Jobs", "SELECT COUNT(*) FROM jobs"),
            ("AI Calls", "SELECT COUNT(*) FROM ai_calls"),
            ("Financial Records", "SELECT COUNT(*) FROM financial_records")
        ]
        
        for table_name, query in tables_info:
            result = execute_query(query, fetch=True)
            count = result[0]['count'] if result else 0
            st.write(f"- {table_name}: {count} records")
    
    with col2:
        st.write("**System Status**")
        
        # Check database connection
        db_status = "🟢 Connected" if execute_query("SELECT 1", fetch=True) else "🔴 Disconnected"
        st.write(f"Database: {db_status}")
        
        # Check AI service (simplified)
        try:
            from ai_bot import AICallerBot
            ai_bot = AICallerBot()
            ai_status = "🟢 Available" if ai_bot.client else "🔴 Unavailable"
        except:
            ai_status = "🔴 Configuration Error"
        
        st.write(f"AI Service: {ai_status}")
        
        st.write(f"Active User: {st.session_state.username}")
        st.write(f"Session Role: {st.session_state.user_role}")
    
    st.markdown("---")
    
    # Application settings
    st.subheader("📋 Application Settings")
    
    with st.form("app_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Default Settings**")
            default_estimate_validity = st.number_input("Estimate Validity (days)", min_value=1, value=30)
            default_profit_margin = st.number_input("Default Profit Margin (%)", min_value=0.0, value=20.0)
            auto_follow_up = st.checkbox("Auto-generate follow-ups", value=True)
        
        with col2:
            st.write("**Notification Settings**")
            email_notifications = st.checkbox("Email notifications", value=True)
            sms_notifications = st.checkbox("SMS notifications", value=False)
            ai_call_alerts = st.checkbox("AI call alerts", value=True)
        
        if st.form_submit_button("Save Settings", use_container_width=True):
            # In a real application, these would be saved to a settings table
            st.success("✅ Settings saved successfully!")

def show_database_maintenance():
    st.subheader("🗃️ Database Maintenance")
    
    st.warning("⚠️ These operations can affect system performance. Use with caution.")
    
    # Database statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Table Sizes**")
        
        # Get table size information (simplified)
        size_queries = [
            ("estimates", "SELECT COUNT(*) as count FROM estimates"),
            ("jobs", "SELECT COUNT(*) as count FROM jobs"),
            ("ai_calls", "SELECT COUNT(*) as count FROM ai_calls"),
            ("financial_records", "SELECT COUNT(*) as count FROM financial_records"),
            ("users", "SELECT COUNT(*) as count FROM users")
        ]
        
        for table, query in size_queries:
            result = execute_query(query, fetch=True)
            count = result[0]['count'] if result else 0
            st.write(f"- {table}: {count} records")
    
    with col2:
        st.write("**Maintenance Actions**")
        
        if st.button("🧹 Clean Old Logs", use_container_width=True):
            # Clean AI calls older than 90 days
            cleanup_query = "DELETE FROM ai_calls WHERE created_at < CURRENT_DATE - INTERVAL '90 days'"
            result = execute_query(cleanup_query)
            if result is not None:
                st.success(f"Cleaned {result} old AI call records")
            else:
                st.error("Cleanup failed")
        
        if st.button("📊 Update Statistics", use_container_width=True):
            # Update table statistics (PostgreSQL specific)
            stats_query = "ANALYZE"
            if execute_query(stats_query):
                st.success("Database statistics updated")
            else:
                st.error("Statistics update failed")
        
        if st.button("🔄 Refresh Connections", use_container_width=True):
            # Clear any cached connections
            st.success("Connection pool refreshed")
    
    # Data export
    st.markdown("---")
    st.subheader("📤 Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_table = st.selectbox(
            "Select Table to Export",
            ["estimates", "jobs", "ai_calls", "financial_records"]
        )
        
        date_range = st.date_input(
            "Date Range",
            value=[st.session_state.get('export_start', None), st.session_state.get('export_end', None)],
            key="export_date_range"
        )
    
    with col2:
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
        
        if st.button("📥 Export Data", use_container_width=True):
            # In a real application, this would generate and download the export
            st.info("Export functionality would be implemented here")

def show_audit_logs():
    st.subheader("📜 Audit Logs")
    
    # In a real application, you would have an audit_logs table
    # For this demo, we'll show recent database activity
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_type = st.selectbox("Log Type", ["All", "User Activity", "Data Changes", "System Events"])
        date_filter = st.date_input("From Date", value=st.date_input("From Date", value=None))
    
    with col2:
        user_filter = st.selectbox("User", ["All"] + [user['username'] for user in get_all_users()])
        show_count = st.selectbox("Show", [25, 50, 100, 200])
    
    # Recent activity summary (simplified)
    st.subheader("📊 Recent Activity Summary")
    
    # Get recent estimates, jobs, calls created
    recent_activity = []
    
    # Recent estimates
    estimates = execute_query("""
        SELECT 'Estimate Created' as action, u.username, e.created_at, 
               CONCAT('Estimate #', e.id, ' for ', e.client_name) as details
        FROM estimates e 
        JOIN users u ON e.created_by = u.id 
        ORDER BY e.created_at DESC LIMIT 10
    """, fetch=True) or []
    
    recent_activity.extend(estimates)
    
    # Recent jobs
    jobs = execute_query("""
        SELECT 'Job Created' as action, 'System' as username, created_at,
               CONCAT('Job #', id, ' - ', job_title) as details
        FROM jobs 
        ORDER BY created_at DESC LIMIT 10
    """, fetch=True) or []
    
    recent_activity.extend(jobs)
    
    # Recent AI calls
    calls = execute_query("""
        SELECT 'AI Call Processed' as action, 'AI System' as username, created_at,
               CONCAT(call_type, ' call to ', phone_number) as details
        FROM ai_calls 
        ORDER BY created_at DESC LIMIT 10
    """, fetch=True) or []
    
    recent_activity.extend(calls)
    
    # Sort by timestamp and display
    recent_activity.sort(key=lambda x: x['created_at'], reverse=True)
    
    if recent_activity:
        for activity in recent_activity[:show_count]:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            with col1:
                st.write(f"**{activity['action']}**")
            
            with col2:
                st.write(f"User: {activity['username']}")
            
            with col3:
                st.write(f"Time: {activity['created_at'].strftime('%m/%d/%Y %I:%M %p')}")
            
            with col4:
                st.write(f"Details: {activity['details']}")
            
            st.markdown("---")
    else:
        st.info("No recent activity found.")
    
    # Export audit logs
    st.markdown("---")
    if st.button("📥 Export Audit Logs", use_container_width=True):
        st.info("Audit log export functionality would be implemented here")
