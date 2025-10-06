import streamlit as st
from database import get_jobs, execute_query, get_estimates
from datetime import datetime, date
import pandas as pd

REQUIRED_ROLE = 'admin'

def show():
    st.markdown("# 🔨 Jobs Management")
    
    tab1, tab2, tab3 = st.tabs(["Active Jobs", "Job Calendar", "Job Analytics"])
    
    with tab1:
        show_active_jobs()
    
    with tab2:
        show_job_calendar()
    
    with tab3:
        show_job_analytics()

def show_active_jobs():
    st.subheader("Job Overview")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "not_started", "in_progress", "completed", "on_hold"],
            key="job_status_filter"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Created Date", "Start Date", "Client Name", "Cost"],
            key="job_sort"
        )
    
    # Get jobs
    jobs = get_jobs() if status_filter == "All" else get_jobs(status_filter)
    
    if jobs:
        # Sort jobs
        if sort_by == "Start Date":
            jobs = sorted(jobs, key=lambda x: x['start_date'] or date.min, reverse=True)
        elif sort_by == "Client Name":
            jobs = sorted(jobs, key=lambda x: x['client_name'])
        elif sort_by == "Cost":
            jobs = sorted(jobs, key=lambda x: x['actual_cost'] or 0, reverse=True)
        
        for job in jobs:
            with st.container():
                # Job header
                col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                
                with col1:
                    st.write(f"**#{job['id']} - {job['job_title']}**")
                    st.write(f"Client: {job['client_name']}")
                    if job['estimate_title']:
                        st.write(f"From Estimate: {job['estimate_title']}")
                
                with col2:
                    if job['actual_cost']:
                        st.write(f"**Cost:** ${job['actual_cost']:,.2f}")
                    else:
                        st.write("**Cost:** TBD")
                    
                    if job['start_date']:
                        st.write(f"**Start:** {job['start_date'].strftime('%m/%d/%Y')}")
                    else:
                        st.write("**Start:** Not scheduled")
                    
                    if job['end_date']:
                        st.write(f"**End:** {job['end_date'].strftime('%m/%d/%Y')}")
                
                with col3:
                    current_status = job['status']
                    status_colors = {
                        'not_started': '⚪',
                        'in_progress': '🟡',
                        'completed': '🟢',
                        'on_hold': '🔴'
                    }
                    st.write(f"{status_colors.get(current_status, '⚪')} {current_status.replace('_', ' ').title()}")
                
                with col4:
                    # Status update
                    new_status = st.selectbox(
                        "Update Status",
                        ["not_started", "in_progress", "completed", "on_hold"],
                        index=["not_started", "in_progress", "completed", "on_hold"].index(current_status),
                        key=f"job_status_{job['id']}"
                    )
                    
                    if st.button("Update", key=f"update_job_{job['id']}", use_container_width=True):
                        update_query = "UPDATE jobs SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                        if execute_query(update_query, (new_status, job['id'])):
                            st.success("Status updated!")
                            st.rerun()
                        else:
                            st.error("Update failed")
                
                # Expandable details
                with st.expander(f"Job #{job['id']} Details", expanded=False):
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.write("**Assigned Crew:**")
                        st.write(job['assigned_crew'] or "Not assigned")
                        
                        st.write("**Profit Margin:**")
                        if job['profit_margin']:
                            st.write(f"{job['profit_margin']}%")
                        else:
                            st.write("Not calculated")
                    
                    with detail_col2:
                        st.write("**Notes:**")
                        st.write(job['notes'] or "No notes")
                        
                        st.write("**Created:**")
                        st.write(job['created_at'].strftime('%m/%d/%Y %I:%M %p'))
                    
                    # Edit job form
                    if st.button(f"Edit Job #{job['id']}", key=f"edit_btn_{job['id']}"):
                        st.session_state[f"edit_job_{job['id']}"] = True
                        st.rerun()
                    
                    if st.session_state.get(f"edit_job_{job['id']}", False):
                        with st.form(f"edit_job_form_{job['id']}"):
                            edit_col1, edit_col2 = st.columns(2)
                            
                            with edit_col1:
                                new_title = st.text_input("Job Title", value=job['job_title'], key=f"edit_title_{job['id']}")
                                new_start_date = st.date_input("Start Date", value=job['start_date'], key=f"edit_start_{job['id']}")
                                new_end_date = st.date_input("End Date", value=job['end_date'], key=f"edit_end_{job['id']}")
                                new_cost = st.number_input("Actual Cost ($)", value=float(job['actual_cost'] or 0), key=f"edit_cost_{job['id']}")
                            
                            with edit_col2:
                                new_crew = st.text_input("Assigned Crew", value=job['assigned_crew'] or "", key=f"edit_crew_{job['id']}")
                                new_margin = st.number_input("Profit Margin (%)", value=float(job['profit_margin'] or 0), key=f"edit_margin_{job['id']}")
                                new_notes = st.text_area("Notes", value=job['notes'] or "", key=f"edit_notes_{job['id']}")
                            
                            form_col1, form_col2 = st.columns(2)
                            with form_col1:
                                if st.form_submit_button("Save Changes", use_container_width=True):
                                    update_query = """
                                        UPDATE jobs SET 
                                            job_title = %s, start_date = %s, end_date = %s, 
                                            actual_cost = %s, assigned_crew = %s, profit_margin = %s, 
                                            notes = %s, updated_at = CURRENT_TIMESTAMP
                                        WHERE id = %s
                                    """
                                    params = (new_title, new_start_date, new_end_date, new_cost, 
                                            new_crew, new_margin, new_notes, job['id'])
                                    
                                    if execute_query(update_query, params):
                                        st.success("Job updated successfully!")
                                        st.session_state[f"edit_job_{job['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to update job")
                            
                            with form_col2:
                                if st.form_submit_button("Cancel", use_container_width=True):
                                    st.session_state[f"edit_job_{job['id']}"] = False
                                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("No jobs found. Jobs are created from approved estimates.")

def show_job_calendar():
    st.subheader("📅 Job Schedule Calendar")
    
    # Get jobs with dates
    jobs = get_jobs()
    scheduled_jobs = [job for job in jobs if job['start_date']]
    
    if scheduled_jobs:
        # Create calendar view
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.write("**Upcoming Jobs:**")
            
            # Sort by start date
            upcoming_jobs = sorted(scheduled_jobs, key=lambda x: x['start_date'])
            
            for job in upcoming_jobs[:10]:  # Show next 10 jobs
                days_until = (job['start_date'] - date.today()).days
                
                if days_until < 0:
                    status_icon = "🔴"  # Overdue
                    date_text = f"Overdue by {abs(days_until)} days"
                elif days_until == 0:
                    status_icon = "🟡"  # Today
                    date_text = "Today"
                elif days_until <= 7:
                    status_icon = "🟠"  # This week
                    date_text = f"In {days_until} days"
                else:
                    status_icon = "🟢"  # Future
                    date_text = f"In {days_until} days"
                
                st.write(f"{status_icon} **{job['job_title']}**")
                st.write(f"   {job['client_name']}")
                st.write(f"   {date_text}")
                st.write("---")
        
        with col2:
            # Calendar visualization using plotly
            import plotly.express as px
            import plotly.graph_objects as go
            
            # Prepare data for timeline chart
            timeline_data = []
            for job in scheduled_jobs:
                end_date = job['end_date'] or job['start_date']
                timeline_data.append({
                    'Job': f"#{job['id']} {job['job_title']}",
                    'Start': job['start_date'],
                    'End': end_date,
                    'Client': job['client_name'],
                    'Status': job['status']
                })
            
            if timeline_data:
                df = pd.DataFrame(timeline_data)
                
                # Create Gantt chart
                fig = px.timeline(
                    df, 
                    x_start="Start", 
                    x_end="End", 
                    y="Job",
                    color="Status",
                    title="Job Timeline",
                    hover_data=["Client"]
                )
                
                fig.update_layout(
                    height=600,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No scheduled jobs found. Schedule jobs by setting start dates.")

def show_job_analytics():
    st.subheader("📊 Job Analytics")
    
    jobs = get_jobs()
    
    if jobs:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j['status'] == 'completed'])
        total_revenue = sum([j['actual_cost'] for j in jobs if j['actual_cost']])
        avg_job_value = total_revenue / total_jobs if total_jobs > 0 else 0
        
        with col1:
            st.metric("Total Jobs", total_jobs)
        with col2:
            st.metric("Completed Jobs", completed_jobs)
        with col3:
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        with col4:
            st.metric("Avg Job Value", f"${avg_job_value:,.2f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_counts = {}
            for job in jobs:
                status = job['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig = px.pie(
                values=list(status_counts.values()),
                names=[s.replace('_', ' ').title() for s in status_counts.keys()],
                title="Job Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly completion trend
            completed_by_month = {}
            for job in jobs:
                if job['status'] == 'completed' and job['end_date']:
                    month_key = job['end_date'].strftime('%Y-%m')
                    completed_by_month[month_key] = completed_by_month.get(month_key, 0) + 1
            
            if completed_by_month:
                months = sorted(completed_by_month.keys())
                counts = [completed_by_month[month] for month in months]
                
                fig = px.bar(
                    x=months,
                    y=counts,
                    title="Jobs Completed by Month"
                )
                fig.update_layout(xaxis_title="Month", yaxis_title="Jobs Completed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No completed jobs with end dates to analyze")
        
        # Profitability analysis
        st.subheader("💰 Profitability Analysis")
        
        profitable_jobs = [j for j in jobs if j['profit_margin']]
        if profitable_jobs:
            df_profit = pd.DataFrame([
                {
                    'Job ID': job['id'],
                    'Job Title': job['job_title'],
                    'Client': job['client_name'],
                    'Cost': job['actual_cost'],
                    'Profit Margin': job['profit_margin'],
                    'Profit Amount': (job['actual_cost'] * job['profit_margin'] / 100) if job['actual_cost'] else 0
                }
                for job in profitable_jobs
            ])
            
            st.dataframe(df_profit, use_container_width=True)
            
            # Average profit margin
            avg_margin = df_profit['Profit Margin'].mean()
            st.metric("Average Profit Margin", f"{avg_margin:.1f}%")
        else:
            st.info("No profit margin data available for analysis")
    else:
        st.info("No jobs available for analysis")
