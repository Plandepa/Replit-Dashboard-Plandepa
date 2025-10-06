import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import get_estimates, get_jobs, get_ai_calls, get_financial_summary
from datetime import datetime, timedelta
import pandas as pd

REQUIRED_ROLE = 'admin'

def show():
    st.markdown("# 📊 Dashboard Overview")
    st.markdown("Welcome to your PLANDEPA management dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Get data for metrics
    estimates = get_estimates()
    jobs = get_jobs()
    ai_calls = get_ai_calls(30)  # Last 30 calls
    financial_data = get_financial_summary()
    
    with col1:
        pending_estimates = len([e for e in estimates if e['status'] == 'pending'])
        st.metric("Pending Estimates", pending_estimates, delta=None)
    
    with col2:
        active_jobs = len([j for j in jobs if j['status'] in ['in_progress', 'started']])
        st.metric("Active Jobs", active_jobs, delta=None)
    
    with col3:
        recent_calls = len([c for c in ai_calls if c['created_at'].date() >= (datetime.now().date() - timedelta(days=7))])
        st.metric("Calls This Week", recent_calls, delta=None)
    
    with col4:
        total_revenue = sum([f['total_amount'] for f in financial_data if f['record_type'] == 'income'])
        st.metric("Total Revenue", f"${total_revenue:,.2f}" if total_revenue else "$0.00", delta=None)
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Estimates Status Distribution")
        if estimates:
            estimate_status = {}
            for estimate in estimates:
                status = estimate['status']
                estimate_status[status] = estimate_status.get(status, 0) + 1
            
            fig = px.pie(
                values=list(estimate_status.values()),
                names=list(estimate_status.keys()),
                title="Estimate Status Breakdown"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No estimates data available")
    
    with col2:
        st.subheader("🔨 Jobs Progress")
        if jobs:
            job_status = {}
            for job in jobs:
                status = job['status']
                job_status[status] = job_status.get(status, 0) + 1
            
            fig = px.bar(
                x=list(job_status.keys()),
                y=list(job_status.values()),
                title="Job Status Overview"
            )
            fig.update_layout(xaxis_title="Status", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No jobs data available")
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    
    tab1, tab2, tab3 = st.tabs(["Recent Estimates", "Recent Jobs", "Recent AI Calls"])
    
    with tab1:
        if estimates:
            recent_estimates = estimates[:5]  # Last 5 estimates
            for estimate in recent_estimates:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.write(f"**{estimate['project_title']}**")
                    with col2:
                        st.write(estimate['client_name'])
                    with col3:
                        st.write(f"${estimate['estimated_cost']:,.2f}" if estimate['estimated_cost'] else "TBD")
                    with col4:
                        status_color = {
                            'pending': '🟡',
                            'approved': '🟢', 
                            'rejected': '🔴',
                            'sent': '🔵'
                        }
                        st.write(f"{status_color.get(estimate['status'], '⚪')} {estimate['status'].title()}")
        else:
            st.info("No recent estimates")
    
    with tab2:
        if jobs:
            recent_jobs = jobs[:5]  # Last 5 jobs
            for job in recent_jobs:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.write(f"**{job['job_title']}**")
                    with col2:
                        st.write(job['client_name'])
                    with col3:
                        if job['start_date']:
                            st.write(job['start_date'].strftime('%m/%d/%Y'))
                        else:
                            st.write("Not scheduled")
                    with col4:
                        status_color = {
                            'not_started': '⚪',
                            'in_progress': '🟡',
                            'completed': '🟢',
                            'on_hold': '🔴'
                        }
                        st.write(f"{status_color.get(job['status'], '⚪')} {job['status'].replace('_', ' ').title()}")
        else:
            st.info("No recent jobs")
    
    with tab3:
        if ai_calls:
            recent_calls = ai_calls[:5]  # Last 5 calls
            for call in recent_calls:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.write(f"**{call['call_type'].title()} Call**")
                    with col2:
                        st.write(call['client_name'] or call['phone_number'])
                    with col3:
                        if call['call_duration']:
                            st.write(f"{call['call_duration']} min")
                        else:
                            st.write("N/A")
                    with col4:
                        status_color = {
                            'completed': '🟢',
                            'failed': '🔴',
                            'initiated': '🟡'
                        }
                        st.write(f"{status_color.get(call['call_status'], '⚪')} {call['call_status'].title()}")
        else:
            st.info("No recent AI calls")
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ New Estimate", use_container_width=True, key="new_estimate_btn"):
            st.session_state.page_nav = "📋 Estimates"
            st.rerun()
    
    with col2:
        if st.button("🔨 Create Job", use_container_width=True, key="new_job_btn"):
            st.session_state.page_nav = "🔨 Jobs"
            st.rerun()
    
    with col3:
        if st.button("📞 AI Call Log", use_container_width=True, key="ai_call_btn"):
            st.session_state.page_nav = "🤖 AI Caller"
            st.rerun()
    
    with col4:
        if st.button("💰 Add Transaction", use_container_width=True, key="transaction_btn"):
            st.session_state.page_nav = "💰 Financials"
            st.rerun()
