import streamlit as st
from database import (
    get_customers, create_customer, get_customer_by_id, update_customer, delete_customer,
    add_customer_contact, get_customer_contacts, update_contact_completed,
    get_pending_follow_ups, get_customer_projects_summary, get_user_by_username
)
from datetime import datetime, date, timedelta
import pandas as pd

REQUIRED_ROLE = 'admin'

def show():
    st.markdown("# 👥 Customer Management")
    st.markdown("Comprehensive customer relationship management system")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Customer List", "Add Customer", "Contact History", "Follow-ups"])
    
    with tab1:
        show_customer_list()
    
    with tab2:
        show_add_customer()
    
    with tab3:
        show_contact_history()
    
    with tab4:
        show_follow_ups()

def show_customer_list():
    st.subheader("📋 Customer Database")
    
    try:
        # Search and filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Search customers", placeholder="Search by name, email, or company...")
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "active", "inactive", "prospect"])
        with col3:
            customer_type_filter = st.selectbox("Customer Type", ["All", "residential", "commercial"])
        
        # Get customers with filters
        status = None if status_filter == "All" else status_filter.lower()
        customers = get_customers(status=status, search=search_term)
        
    except Exception as e:
        st.error("Unable to load customer data. Please refresh the page.")
        return
    
    # Filter by customer type
    if customer_type_filter != "All":
        customers = [c for c in customers if c['customer_type'] == customer_type_filter.lower()]
    
    # Customer metrics
    if customers:
        total_customers = len(customers)
        active_customers = len([c for c in customers if c['status'] == 'active'])
        commercial_customers = len([c for c in customers if c['customer_type'] == 'commercial'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Customers", total_customers)
        with col2:
            st.metric("Active Customers", active_customers)
        with col3:
            st.metric("Commercial", commercial_customers)
        with col4:
            residential_customers = total_customers - commercial_customers
            st.metric("Residential", residential_customers)
        
        st.markdown("---")
        
        # Customer list
        for customer in customers:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    full_name = f"{customer['first_name']} {customer['last_name']}"
                    st.write(f"**{full_name}**")
                    if customer['company_name']:
                        st.write(f"Company: {customer['company_name']}")
                    st.write(f"Email: {customer['email'] or 'Not provided'}")
                    st.write(f"Phone: {customer['phone'] or 'Not provided'}")
                
                with col2:
                    st.write(f"**Type:** {customer['customer_type'].title()}")
                    status_colors = {'active': '🟢', 'inactive': '🔴', 'prospect': '🟡'}
                    st.write(f"**Status:** {status_colors.get(customer['status'], '⚪')} {customer['status'].title()}")
                    st.write(f"**Lead Source:** {customer['lead_source'] or 'Unknown'}")
                
                with col3:
                    # Get project summary
                    summary = get_customer_projects_summary(customer['id'])
                    st.write(f"**Estimates:** {summary['total_estimates']}")
                    st.write(f"**Jobs:** {summary['total_jobs']}")
                    st.write(f"**Revenue:** ${summary['total_revenue']:,.2f}")
                
                with col4:
                    if st.button("👁️ View", key=f"view_{customer['id']}", use_container_width=True):
                        st.session_state[f"view_customer_{customer['id']}"] = True
                        st.rerun()
                    
                    if st.button("✏️ Edit", key=f"edit_{customer['id']}", use_container_width=True):
                        st.session_state[f"edit_customer_{customer['id']}"] = True
                        st.rerun()
                
                # Customer detail view
                if st.session_state.get(f"view_customer_{customer['id']}", False):
                    show_customer_details(customer)
                
                # Edit customer form
                if st.session_state.get(f"edit_customer_{customer['id']}", False):
                    show_edit_customer_form(customer)
                
                st.markdown("---")
    else:
        st.info("No customers found. Add your first customer using the 'Add Customer' tab.")

def show_customer_details(customer):
    """Show detailed customer information"""
    with st.expander(f"👤 Customer Details: {customer['first_name']} {customer['last_name']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Contact Information:**")
            st.write(f"Name: {customer['first_name']} {customer['last_name']}")
            st.write(f"Email: {customer['email'] or 'Not provided'}")
            st.write(f"Phone: {customer['phone'] or 'Not provided'}")
            if customer['company_name']:
                st.write(f"Company: {customer['company_name']}")
            
            st.write("\n**Address:**")
            if customer['address']:
                st.write(f"{customer['address']}")
                if customer['city'] or customer['state'] or customer['zip_code']:
                    address_line2 = f"{customer['city'] or ''}, {customer['state'] or ''} {customer['zip_code'] or ''}".strip(', ')
                    st.write(address_line2)
            else:
                st.write("No address on file")
        
        with col2:
            st.write("**Customer Information:**")
            st.write(f"Type: {customer['customer_type'].title()}")
            st.write(f"Status: {customer['status'].title()}")
            st.write(f"Lead Source: {customer['lead_source'] or 'Unknown'}")
            st.write(f"Created: {customer['created_at'].strftime('%m/%d/%Y')}")
            
            if customer['notes']:
                st.write("\n**Notes:**")
                st.text_area("", value=customer['notes'], height=100, disabled=True, key=f"notes_view_{customer['id']}")
        
        # Project summary
        summary = get_customer_projects_summary(customer['id'])
        st.write("**Project Summary:**")
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            st.metric("Total Estimates", summary['total_estimates'])
        with summary_col2:
            st.metric("Approved Estimates", summary['approved_estimates'])
        with summary_col3:
            st.metric("Total Jobs", summary['total_jobs'])
        with summary_col4:
            st.metric("Total Revenue", f"${summary['total_revenue']:,.2f}")
        
        # Recent contacts
        contacts = get_customer_contacts(customer['id'], limit=5)
        if contacts:
            st.write("\n**Recent Contacts:**")
            for contact in contacts:
                contact_col1, contact_col2 = st.columns([3, 1])
                with contact_col1:
                    st.write(f"• **{contact['contact_type'].title()}:** {contact['subject']}")
                    st.write(f"  {contact['contact_date'].strftime('%m/%d/%Y %I:%M %p')}")
                with contact_col2:
                    if contact['follow_up_date'] and not contact['completed']:
                        st.write("🔔 Follow-up needed")
        
        # Close button
        if st.button("Close Details", key=f"close_view_{customer['id']}"):
            st.session_state[f"view_customer_{customer['id']}"] = False
            st.rerun()

def show_edit_customer_form(customer):
    """Show customer edit form"""
    with st.expander(f"✏️ Edit Customer: {customer['first_name']} {customer['last_name']}", expanded=True):
        with st.form(f"edit_customer_form_{customer['id']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name *", value=customer['first_name'])
                last_name = st.text_input("Last Name *", value=customer['last_name'])
                email = st.text_input("Email", value=customer['email'] or '')
                phone = st.text_input("Phone", value=customer['phone'] or '')
                company_name = st.text_input("Company Name", value=customer['company_name'] or '')
            
            with col2:
                address = st.text_area("Address", value=customer['address'] or '')
                city = st.text_input("City", value=customer['city'] or '')
                state = st.text_input("State", value=customer['state'] or '')
                zip_code = st.text_input("ZIP Code", value=customer['zip_code'] or '')
            
            col3, col4 = st.columns(2)
            with col3:
                customer_type = st.selectbox(
                    "Customer Type",
                    ["residential", "commercial"],
                    index=0 if customer['customer_type'] == 'residential' else 1
                )
                status = st.selectbox(
                    "Status",
                    ["active", "inactive", "prospect"],
                    index=["active", "inactive", "prospect"].index(customer['status'])
                )
            
            with col4:
                lead_source = st.text_input("Lead Source", value=customer['lead_source'] or '')
                notes = st.text_area("Notes", value=customer['notes'] or '')
            
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    if first_name and last_name:
                        customer_data = {
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email if email else None,
                            'phone': phone if phone else None,
                            'address': address if address else None,
                            'city': city if city else None,
                            'state': state if state else None,
                            'zip_code': zip_code if zip_code else None,
                            'company_name': company_name if company_name else None,
                            'customer_type': customer_type,
                            'lead_source': lead_source if lead_source else None,
                            'status': status,
                            'notes': notes if notes else None
                        }
                        
                        if update_customer(customer['id'], customer_data):
                            st.success("✅ Customer updated successfully!")
                            st.session_state[f"edit_customer_{customer['id']}"] = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to update customer")
                    else:
                        st.error("❌ First name and last name are required")
            
            with form_col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state[f"edit_customer_{customer['id']}"] = False
                    st.rerun()

def show_add_customer():
    st.subheader("➕ Add New Customer")
    
    with st.form("add_customer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Contact Information:**")
            first_name = st.text_input("First Name *", placeholder="John")
            last_name = st.text_input("Last Name *", placeholder="Smith")
            email = st.text_input("Email", placeholder="john.smith@email.com")
            phone = st.text_input("Phone", placeholder="(555) 123-4567")
            company_name = st.text_input("Company Name", placeholder="Smith Construction LLC")
        
        with col2:
            st.write("**Address Information:**")
            address = st.text_area("Address", placeholder="123 Main Street")
            city = st.text_input("City", placeholder="Springfield")
            state = st.text_input("State", placeholder="IL")
            zip_code = st.text_input("ZIP Code", placeholder="62701")
        
        col3, col4 = st.columns(2)
        with col3:
            customer_type = st.selectbox("Customer Type", ["residential", "commercial"])
            status = st.selectbox("Status", ["prospect", "active", "inactive"])
        
        with col4:
            lead_source = st.selectbox(
                "Lead Source",
                ["Website", "Referral", "Advertisement", "Cold Call", "Social Media", "Trade Show", "Other"]
            )
            notes = st.text_area("Notes", placeholder="Additional information about the customer...")
        
        if st.form_submit_button("➕ Add Customer", use_container_width=True):
            if first_name and last_name:
                customer_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email if email else None,
                    'phone': phone if phone else None,
                    'address': address if address else None,
                    'city': city if city else None,
                    'state': state if state else None,
                    'zip_code': zip_code if zip_code else None,
                    'company_name': company_name if company_name else None,
                    'customer_type': customer_type,
                    'lead_source': lead_source.lower() if lead_source != "Other" else "other",
                    'notes': notes if notes else None
                }
                
                customer_id = create_customer(customer_data)
                if customer_id:
                    st.success(f"✅ Customer '{first_name} {last_name}' added successfully! (ID: #{customer_id})")
                    st.rerun()
                else:
                    st.error("❌ Failed to add customer. Email might already exist.")
            else:
                st.error("❌ First name and last name are required")

def show_contact_history():
    st.subheader("📞 Contact History Management")
    
    # Add new contact
    with st.expander("➕ Add New Contact Record", expanded=False):
        with st.form("add_contact_form"):
            col1, col2 = st.columns(2)
            
            # Initialize variables
            customers = get_customers()
            selected_customer = None
            contact_type = None
            subject = None
            
            with col1:
                # Customer selection
                if customers:
                    customer_options = [f"{c['first_name']} {c['last_name']} - {c['company_name'] or 'No Company'}" for c in customers]
                    selected_customer_idx = st.selectbox("Select Customer", range(len(customer_options)), format_func=lambda x: customer_options[x])
                    selected_customer = customers[selected_customer_idx]
                    
                    contact_type = st.selectbox(
                        "Contact Type",
                        ["Phone Call", "Email", "In-Person Meeting", "Site Visit", "Follow-up", "Complaint", "Quote Request"]
                    )
                    subject = st.text_input("Subject *", placeholder="Brief description of contact...")
                else:
                    st.info("No customers found. Add customers first.")
            
            with col2:
                contact_date = st.date_input("Contact Date", value=datetime.now().date())
                contact_time = st.time_input("Contact Time", value=datetime.now().time())
                follow_up_date = st.date_input("Follow-up Date (Optional)", value=None)
                description = st.text_area("Description", placeholder="Detailed notes about this contact...")
            
            if st.form_submit_button("➕ Add Contact Record", use_container_width=True):
                if customers and selected_customer and subject and contact_type:
                    user = get_user_by_username(st.session_state.username)
                    
                    # Combine date and time
                    contact_datetime = datetime.combine(contact_date, contact_time)
                    
                    contact_data = {
                        'customer_id': selected_customer['id'],
                        'contact_type': contact_type.lower().replace(' ', '_'),
                        'subject': subject,
                        'description': description if description else None,
                        'contact_date': contact_datetime,
                        'follow_up_date': follow_up_date,
                        'created_by': user['id'] if user else None
                    }
                    
                    contact_id = add_customer_contact(contact_data)
                    if contact_id:
                        st.success(f"✅ Contact record added successfully! (ID: #{contact_id})")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add contact record")
                else:
                    if not customers:
                        st.error("❌ No customers found. Add customers first.")
                    elif not subject:
                        st.error("❌ Subject is required")
                    else:
                        st.error("❌ Please fill in all required fields")
    
    # Recent contacts across all customers
    st.subheader("📋 Recent Contact Activity")
    
    # Get recent contacts from all customers
    all_contacts = []
    customers = get_customers()
    for customer in customers[:20]:  # Limit to prevent performance issues
        contacts = get_customer_contacts(customer['id'], limit=10)
        for contact in contacts:
            contact['customer_name'] = f"{customer['first_name']} {customer['last_name']}"
            contact['company_name'] = customer['company_name']
            all_contacts.append(contact)
    
    # Sort by contact date
    all_contacts.sort(key=lambda x: x['contact_date'], reverse=True)
    
    if all_contacts:
        for contact in all_contacts[:20]:  # Show last 20 contacts
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{contact['customer_name']}**")
                    if contact['company_name']:
                        st.write(f"Company: {contact['company_name']}")
                
                with col2:
                    st.write(f"**{contact['contact_type'].replace('_', ' ').title()}**")
                    st.write(f"Subject: {contact['subject']}")
                
                with col3:
                    st.write(f"**Date:** {contact['contact_date'].strftime('%m/%d/%Y %I:%M %p')}")
                    if contact['follow_up_date']:
                        follow_up_status = "✅ Completed" if contact['completed'] else "🔔 Pending"
                        st.write(f"**Follow-up:** {follow_up_status}")
                
                with col4:
                    if contact['follow_up_date'] and not contact['completed']:
                        if st.button("✅ Complete", key=f"complete_{contact['id']}", use_container_width=True):
                            if update_contact_completed(contact['id'], True):
                                st.success("Follow-up marked complete!")
                                st.rerun()
                
                if contact['description']:
                    with st.expander(f"Notes - {contact['subject']}", expanded=False):
                        st.write(contact['description'])
                        st.write(f"*Added by: {contact.get('created_by_name', 'Unknown')}*")
                
                st.markdown("---")
    else:
        st.info("No contact records found. Add contact records using the form above.")

def show_follow_ups():
    st.subheader("🔔 Pending Follow-ups")
    
    pending_followups = get_pending_follow_ups()
    
    if pending_followups:
        # Sort by follow-up date
        overdue = [f for f in pending_followups if f['follow_up_date'] < date.today()]
        today = [f for f in pending_followups if f['follow_up_date'] == date.today()]
        upcoming = [f for f in pending_followups if f['follow_up_date'] > date.today()]
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pending", len(pending_followups))
        with col2:
            st.metric("Overdue", len(overdue), delta=f"-{len(overdue)}" if overdue else None)
        with col3:
            st.metric("Due Today", len(today))
        with col4:
            st.metric("Upcoming", len(upcoming))
        
        st.markdown("---")
        
        # Show overdue first
        if overdue:
            st.error("🚨 **Overdue Follow-ups**")
            for followup in overdue:
                show_followup_item(followup, "overdue")
        
        # Show today's follow-ups
        if today:
            st.warning("⏰ **Due Today**")
            for followup in today:
                show_followup_item(followup, "today")
        
        # Show upcoming
        if upcoming:
            st.info("📅 **Upcoming Follow-ups**")
            for followup in upcoming[:10]:  # Limit to next 10
                show_followup_item(followup, "upcoming")
    else:
        st.success("🎉 All caught up! No pending follow-ups.")

def show_followup_item(followup, category):
    """Display a single follow-up item"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            customer_name = f"{followup['first_name']} {followup['last_name']}"
            st.write(f"**{customer_name}**")
            if followup['company_name']:
                st.write(f"Company: {followup['company_name']}")
            st.write(f"Subject: {followup['subject']}")
        
        with col2:
            st.write(f"**Type:** {followup['contact_type'].replace('_', ' ').title()}")
            st.write(f"**Original Contact:** {followup['contact_date'].strftime('%m/%d/%Y')}")
        
        with col3:
            days_diff = (followup['follow_up_date'] - date.today()).days
            if days_diff < 0:
                st.write(f"**Due:** {abs(days_diff)} days overdue")
            elif days_diff == 0:
                st.write("**Due:** Today")
            else:
                st.write(f"**Due:** In {days_diff} days")
            
            st.write(f"**Added by:** {followup.get('created_by_name', 'Unknown')}")
        
        with col4:
            if st.button("✅ Complete", key=f"complete_followup_{followup['id']}", use_container_width=True):
                if update_contact_completed(followup['id'], True):
                    st.success("Follow-up completed!")
                    st.rerun()
        
        st.markdown("---")