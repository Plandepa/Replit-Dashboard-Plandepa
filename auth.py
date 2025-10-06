import hashlib
import streamlit as st
from database import get_user_by_username, execute_query
from datetime import datetime

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """Authenticate user credentials"""
    try:
        user = get_user_by_username(username)
        if user and user['password_hash'] == hash_password(password):
            # Update last login
            query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
            execute_query(query, (user['id'],))
            
            return {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'full_name': user['full_name'],
                'email': user['email']
            }
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def check_permissions(user_role, required_role):
    """Check if user has required permissions"""
    role_hierarchy = {
        'super_admin': 3,
        'admin': 2,
        'user': 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 2)
    
    return user_level >= required_level

def create_user(username, password, role, full_name, email):
    """Create new user"""
    try:
        password_hash = hash_password(password)
        query = """
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        result = execute_query(query, (username, password_hash, role, full_name, email), fetch=True)
        return result[0]['id'] if result else None
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return None

def get_all_users():
    """Get all users (super admin only)"""
    query = "SELECT id, username, role, full_name, email, created_at, last_login FROM users ORDER BY created_at DESC"
    return execute_query(query, fetch=True) or []

def update_user_role(user_id, new_role):
    """Update user role"""
    query = "UPDATE users SET role = %s WHERE id = %s"
    return execute_query(query, (new_role, user_id))
