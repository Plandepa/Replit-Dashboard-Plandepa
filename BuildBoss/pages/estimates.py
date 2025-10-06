import streamlit as st
from database import create_estimate, get_estimates, update_estimate_status, create_job_from_estimate, get_user_by_username
from datetime import datetime, date
from ai_bot import AICallerBot

REQUIRED_ROLE = 'admin'

def show():
    st.markdown("# 📋 Estimates Management")
    
    tab1, tab2, tab3 = st.tabs(["Create Estimate", "Manage Estimates", "AI Cost Analysis"])
    
    with tab1:
        show_create_estimate()
    
    with tab2:
        show_manage_estimates()
    
    with tab3:
        show_ai_cost_analysis()

def show_create_estimate():
    st.subheader("Create New Estimate")
    
    with st.form("create_estimate_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("Client Name *", placeholder="Enter client full name")
            client_email = st.text_input("Client Email", placeholder="client@email.com")
            project_title = st.text_input("Project Title *", placeholder="Kitchen Renovation, Deck Construction, etc.")
            estimated_cost = st.number_input("Estimated Cost ($)", min_value=0.0, format="%.2f")
        
        with col2:
            client_phone = st.text_input("Client Phone", placeholder="(555) 123-4567")
            description = st.text_area("Project Description", placeholder="Detailed description of the project scope, materials, timeline, etc.", height=150)
        
        submitted = st.form_submit_button("Create Estimate", use_container_width=True)
        
        if submitted:
            if client_name and project_title:
                # Get current user ID
                user = get_user_by_username(st.session_state.username)
                
                estimate_data = {
                    'client_name': client_name,
                    'client_email': client_email or None,
                    'client_phone': client_phone or None,
                    'project_title': project_title,
                    'description': description or None,
                    'estimated_cost': estimated_cost if estimated_cost > 0 else None,
                    'created_by': user['id'] if user else None
                }
                
                estimate_id = create_estimate(estimate_data)
                if estimate_id:
                    st.success(f"✅ Estimate #{estimate_id} created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create estimate. Please try again.")
            else:
                st.error("❌ Please fill in all required fields (marked with *)")

def show_manage_estimates():
    st.subheader("Existing Estimates")
    
    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "sent", "approved", "rejected"],
            key="estimate_status_filter"
        )
    
    # Get estimates
    estimates = get_estimates() if status_filter == "All" else get_estimates(status_filter.lower())
    
    if estimates:
        for estimate in estimates:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                
                with col1:
                    st.write(f"**#{estimate['id']} - {estimate['project_title']}**")
                    st.write(f"Client: {estimate['client_name']}")
                    if estimate['description']:
                        st.write(f"Description: {estimate['description'][:100]}...")
                
                with col2:
                    st.write(f"**Cost:** ${estimate['estimated_cost']:,.2f}" if estimate['estimated_cost'] else "Cost: TBD")
                    st.write(f"**Created:** {estimate['created_at'].strftime('%m/%d/%Y')}")
                
                with col3:
                    current_status = estimate['status']
                    status_colors = {
                        'pending': '🟡',
                        'sent': '🔵',
                        'approved': '🟢',
                        'rejected': '🔴'
                    }
                    st.write(f"{status_colors.get(current_status, '⚪')} {current_status.title()}")
                
                with col4:
                    # Status update dropdown
                    new_status = st.selectbox(
                        "Update Status",
                        ["pending", "sent", "approved", "rejected"],
                        index=["pending", "sent", "approved", "rejected"].index(current_status),
                        key=f"status_{estimate['id']}"
                    )
                    
                    col4a, col4b = st.columns(2)
                    with col4a:
                        if st.button("Update", key=f"update_{estimate['id']}", use_container_width=True):
                            if update_estimate_status(estimate['id'], new_status):
                                st.success("Status updated!")
                                st.rerun()
                            else:
                                st.error("Update failed")
                    
                    with col4b:
                        if new_status == "approved" and st.button("Create Job", key=f"job_{estimate['id']}", use_container_width=True):
                            st.session_state[f"create_job_{estimate['id']}"] = True
                            st.rerun()
                
                # Job creation form (appears when "Create Job" is clicked)
                if st.session_state.get(f"create_job_{estimate['id']}", False):
                    with st.expander(f"Create Job from Estimate #{estimate['id']}", expanded=True):
                        with st.form(f"job_form_{estimate['id']}"):
                            job_col1, job_col2 = st.columns(2)
                            
                            with job_col1:
                                job_title = st.text_input("Job Title", value=estimate['project_title'], key=f"job_title_{estimate['id']}")
                                start_date = st.date_input("Start Date", key=f"start_date_{estimate['id']}")
                                actual_cost = st.number_input("Actual Cost ($)", value=float(estimate['estimated_cost'] or 0), key=f"actual_cost_{estimate['id']}")
                            
                            with job_col2:
                                assigned_crew = st.text_input("Assigned Crew", placeholder="Team Alpha, John Smith, etc.", key=f"crew_{estimate['id']}")
                                notes = st.text_area("Job Notes", placeholder="Special instructions, materials needed, etc.", key=f"notes_{estimate['id']}")
                            
                            job_col1, job_col2 = st.columns(2)
                            with job_col1:
                                if st.form_submit_button("Create Job", use_container_width=True):
                                    job_data = {
                                        'job_title': job_title,
                                        'client_name': estimate['client_name'],
                                        'start_date': start_date,
                                        'actual_cost': actual_cost,
                                        'assigned_crew': assigned_crew,
                                        'notes': notes
                                    }
                                    
                                    job_id = create_job_from_estimate(estimate['id'], job_data)
                                    if job_id:
                                        st.success(f"✅ Job #{job_id} created successfully!")
                                        st.session_state[f"create_job_{estimate['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to create job")
                            
                            with job_col2:
                                if st.form_submit_button("Cancel", use_container_width=True):
                                    st.session_state[f"create_job_{estimate['id']}"] = False
                                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("No estimates found. Create your first estimate using the form above.")

def show_ai_cost_analysis():
    st.subheader("🤖 AI Cost Analysis")
    st.write("Use AI to help estimate project costs based on descriptions")
    
    with st.form("ai_cost_analysis"):
        project_description = st.text_area(
            "Project Description",
            placeholder="Describe the project in detail: type of work, materials needed, square footage, complexity, etc.",
            height=150
        )
        
        if st.form_submit_button("Analyze with AI", use_container_width=True):
            if project_description.strip():
                with st.spinner("Analyzing project with AI..."):
                    ai_bot = AICallerBot()
                    estimate = ai_bot.estimate_project_cost(project_description)
                    
                    if estimate:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("💰 Cost Estimate")
                            st.metric("Low Estimate", f"${estimate['low_estimate']:,.2f}")
                            st.metric("High Estimate", f"${estimate['high_estimate']:,.2f}")
                            st.metric("Materials Cost", f"${estimate['materials_cost']:,.2f}")
                            st.metric("Labor Cost", f"${estimate['labor_cost']:,.2f}")
                        
                        with col2:
                            st.subheader("📊 Project Details")
                            st.metric("Timeline", f"{estimate['timeline_days']} days")
                            st.metric("Complexity", estimate['complexity_rating'].title())
                            
                            st.subheader("🔍 Key Factors")
                            for factor in estimate.get('key_factors', []):
                                st.write(f"• {factor}")
                        
                        # Option to create estimate from AI analysis
                        st.markdown("---")
                        st.subheader("Create Estimate from AI Analysis")
                        
                        with st.form("create_from_ai"):
                            ai_col1, ai_col2 = st.columns(2)
                            
                            with ai_col1:
                                ai_client_name = st.text_input("Client Name")
                                ai_client_email = st.text_input("Client Email")
                                ai_project_title = st.text_input("Project Title")
                            
                            with ai_col2:
                                ai_client_phone = st.text_input("Client Phone")
                                suggested_cost = (estimate['low_estimate'] + estimate['high_estimate']) / 2
                                ai_estimated_cost = st.number_input("Final Estimate ($)", value=suggested_cost, format="%.2f")
                            
                            if st.form_submit_button("Create Estimate", use_container_width=True):
                                if ai_client_name and ai_project_title:
                                    user = get_user_by_username(st.session_state.username)
                                    
                                    ai_estimate_data = {
                                        'client_name': ai_client_name,
                                        'client_email': ai_client_email or None,
                                        'client_phone': ai_client_phone or None,
                                        'project_title': ai_project_title,
                                        'description': f"AI Analysis: {project_description}",
                                        'estimated_cost': ai_estimated_cost,
                                        'created_by': user['id'] if user else None
                                    }
                                    
                                    estimate_id = create_estimate(ai_estimate_data)
                                    if estimate_id:
                                        st.success(f"✅ Estimate #{estimate_id} created from AI analysis!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to create estimate")
                                else:
                                    st.error("❌ Please fill in client name and project title")
                    else:
                        st.error("❌ Failed to analyze project. Please try again.")
            else:
                st.error("❌ Please enter a project description")
