import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    get_invoices, get_invoice_details, create_invoice, add_invoice_item,
    update_payment_status, generate_invoice_from_job, get_overdue_invoices,
    get_invoice_statistics, get_customers, get_jobs
)

# Page configuration
REQUIRED_ROLE = 'admin'

def show():
    """Main invoices management page"""
    st.title("💰 Invoice Management")
    
    # Invoice statistics overview
    show_invoice_stats()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 All Invoices", 
        "➕ Create Invoice", 
        "📄 Invoice Details", 
        "⚠️ Overdue Invoices",
        "💳 Payment Tracking"
    ])
    
    with tab1:
        show_all_invoices()
    
    with tab2:
        show_create_invoice()
    
    with tab3:
        show_invoice_details()
    
    with tab4:
        show_overdue_invoices()
    
    with tab5:
        show_payment_tracking()

def show_invoice_stats():
    """Display invoice statistics dashboard"""
    stats = get_invoice_statistics()
    
    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Invoices",
                stats.get('total_invoices', 0)
            )
        
        with col2:
            st.metric(
                "Paid Invoices", 
                stats.get('paid_invoices', 0),
                delta=f"{stats.get('paid_invoices', 0)}/{stats.get('total_invoices', 0)} paid"
            )
        
        with col3:
            st.metric(
                "Total Billed",
                f"${stats.get('total_billed', 0):,.2f}"
            )
        
        with col4:
            st.metric(
                "Collected",
                f"${stats.get('total_collected', 0):,.2f}"
            )
        
        with col5:
            overdue_count = stats.get('overdue_invoices', 0)
            st.metric(
                "Overdue",
                overdue_count,
                delta=f"-${stats.get('outstanding_amount', 0):,.2f}" if overdue_count > 0 else None
            )
    
    st.markdown("---")

def show_all_invoices():
    """Display all invoices with filtering"""
    st.subheader("All Invoices")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "unpaid", "paid", "partial", "overdue"],
            key="invoice_status_filter"
        )
    
    with col2:
        customers = get_customers()
        customer_options = ["All Customers"] + [f"{c['first_name']} {c['last_name']}" for c in customers]
        customer_filter = st.selectbox("Filter by Customer", customer_options)
    
    with col3:
        st.write("") # Spacing
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get filtered invoices
    status = None if status_filter == "All" else status_filter
    customer_id = None
    
    if customer_filter != "All Customers":
        for c in customers:
            if f"{c['first_name']} {c['last_name']}" == customer_filter:
                customer_id = c['id']
                break
    
    try:
        invoices = get_invoices(status=status, customer_id=customer_id)
    except Exception as e:
        st.error(f"Error loading invoices: {str(e)}")
        return
    
    if invoices:
        # Create DataFrame for display
        invoice_data = []
        for invoice in invoices:
            customer_name = f"{invoice.get('first_name', '')} {invoice.get('last_name', '')}"
            
            # Determine status badge
            status_color = {
                'paid': '🟢', 'unpaid': '🔴', 'partial': '🟡', 'overdue': '🔴'
            }
            
            invoice_data.append({
                "Invoice #": invoice['invoice_number'],
                "Customer": customer_name,
                "Job": invoice.get('job_title', 'N/A'),
                "Amount": f"${invoice['total_amount']:,.2f}",
                "Paid": f"${invoice.get('paid_amount', 0):,.2f}",
                "Status": f"{status_color.get(invoice['payment_status'], '⚪')} {invoice['payment_status'].title()}",
                "Due Date": invoice['due_date'].strftime('%Y-%m-%d') if invoice['due_date'] else 'N/A',
                "ID": invoice['id']
            })
        
        df = pd.DataFrame(invoice_data)
        st.dataframe(
            df.drop('ID', axis=1), 
            use_container_width=True,
            height=400
        )
        
        # Quick actions
        st.subheader("Quick Actions")
        
        if invoice_data:
            selected_invoice = st.selectbox(
                "Select Invoice for Actions",
                options=[f"{row['Invoice #']} - {row['Customer']}" for row in invoice_data],
                key="selected_invoice_action"
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 View Details"):
                    # Find invoice ID
                    for row in invoice_data:
                        if f"{row['Invoice #']} - {row['Customer']}" == selected_invoice:
                            st.session_state.invoice_detail_id = row['ID']
                            st.rerun()
                            break
            
            with col2:
                if st.button("💰 Record Payment"):
                    # Find invoice ID for payment
                    for row in invoice_data:
                        if f"{row['Invoice #']} - {row['Customer']}" == selected_invoice:
                            st.session_state.payment_invoice_id = row['ID']
                            st.rerun()
                            break
            
            with col3:
                if st.button("📧 Send Reminder"):
                    st.success("Reminder email sent! (Feature simulated)")
    
    else:
        st.info("No invoices found matching your criteria.")

def show_create_invoice():
    """Create new invoice form"""
    st.subheader("Create New Invoice")
    
    # Choose creation method
    creation_method = st.radio(
        "How would you like to create the invoice?",
        ["Manual Invoice", "From Completed Job"],
        key="invoice_creation_method"
    )
    
    if creation_method == "From Completed Job":
        show_create_from_job()
    else:
        show_manual_invoice_creation()

def show_create_from_job():
    """Create invoice from completed job"""
    st.markdown("### Generate Invoice from Completed Job")
    
    # Get completed jobs
    try:
        jobs = get_jobs(status='completed')
    except Exception as e:
        st.error(f"Error loading completed jobs: {str(e)}")
        return
    
    if not jobs:
        st.warning("No completed jobs available for invoicing.")
        st.info("💡 Complete some jobs first to generate invoices automatically.")
        return
    
    # Filter out jobs that already have invoices
    available_jobs = []
    for job in jobs:
        # Check if job already has invoice (simplified check)
        existing_invoices = get_invoices()
        has_invoice = any(inv.get('job_id') == job['id'] for inv in existing_invoices)
        if not has_invoice:
            available_jobs.append(job)
    
    if not available_jobs:
        st.warning("All completed jobs already have invoices generated.")
        return
    
    # Job selection
    job_options = [f"{job['job_title']} - ${job.get('actual_cost', 0):,.2f}" for job in available_jobs]
    selected_job_idx = st.selectbox(
        "Select Completed Job",
        range(len(job_options)),
        format_func=lambda x: job_options[x],
        key="job_for_invoice"
    )
    
    if selected_job_idx is not None:
        selected_job = available_jobs[selected_job_idx]
        
        # Display job details
        st.markdown("#### Job Details")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Job:** {selected_job['job_title']}")
            st.write(f"**Status:** {selected_job['status']}")
            st.write(f"**Completion Date:** {selected_job.get('end_date', 'N/A')}")
        
        with col2:
            st.write(f"**Cost:** ${selected_job.get('actual_cost', 0):,.2f}")
            st.write(f"**Client:** {selected_job.get('client_name', 'N/A')}")
        
        # Invoice settings
        st.markdown("#### Invoice Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            tax_rate = st.number_input("Tax Rate (%)", value=8.0, min_value=0.0, max_value=20.0, step=0.5)
        
        with col2:
            payment_terms = st.selectbox("Payment Terms", ["Net 30", "Net 15", "Due on Receipt"])
        
        # Calculate totals
        subtotal = float(selected_job.get('actual_cost', 0))
        tax_amount = subtotal * (tax_rate / 100)
        total_amount = subtotal + tax_amount
        
        st.markdown("#### Invoice Preview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Subtotal", f"${subtotal:,.2f}")
        with col2:
            st.metric("Tax", f"${tax_amount:,.2f}")
        with col3:
            st.metric("Total", f"${total_amount:,.2f}")
        
        # Generate invoice button
        if st.button("🧾 Generate Invoice", type="primary"):
            try:
                invoice_id = generate_invoice_from_job(
                    selected_job['id'], 
                    st.session_state.user['id']
                )
                
                if invoice_id:
                    st.success(f"✅ Invoice generated successfully! Invoice ID: {invoice_id}")
                    
                    # Add to financial records
                    try:
                        from database import add_financial_record
                        from datetime import date
                        add_financial_record({
                            'record_type': 'income',
                            'amount': total_amount,
                            'description': f"Invoice generated for job: {selected_job['job_title']}",
                            'category': 'invoice_generation',
                            'job_id': selected_job['id'],
                            'transaction_date': date.today()
                        })
                    except Exception as e:
                        st.warning(f"Invoice created successfully, but failed to update financial records: {str(e)}")
                    
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to generate invoice. Please try again.")
                    
            except Exception as e:
                st.error(f"Error generating invoice: {str(e)}")

def show_manual_invoice_creation():
    """Manual invoice creation form"""
    st.markdown("### Manual Invoice Creation")
    
    with st.form("manual_invoice_form"):
        # Customer selection
        try:
            customers = get_customers()
        except Exception as e:
            st.error(f"Error loading customers: {str(e)}")
            return
        
        if not customers:
            st.warning("No customers available for invoicing.")
            st.info("💡 Add customers first in the Customers section before creating manual invoices.")
            return
        
        customer_options = [f"{c['first_name']} {c['last_name']} ({c['email']})" for c in customers]
        
        selected_customer_idx = st.selectbox(
            "Select Customer",
            range(len(customer_options)),
            format_func=lambda x: customer_options[x] if x < len(customer_options) else "Select...",
            key="manual_invoice_customer"
        )
        
        # Invoice details
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_date = st.date_input("Invoice Date", value=date.today())
            payment_terms = st.selectbox("Payment Terms", ["Net 30", "Net 15", "Due on Receipt"])
        
        with col2:
            due_days = {"Net 30": 30, "Net 15": 15, "Due on Receipt": 0}
            due_date = st.date_input(
                "Due Date", 
                value=date.today() + timedelta(days=due_days[payment_terms])
            )
            tax_rate = st.number_input("Tax Rate (%)", value=8.0, min_value=0.0, max_value=20.0)
        
        # Line items
        st.markdown("#### Invoice Items")
        
        # Initialize line items in session state
        if 'manual_invoice_items' not in st.session_state:
            st.session_state.manual_invoice_items = [
                {"description": "", "quantity": 1.0, "unit_price": 0.0}
            ]
        
        # Display current items
        total_subtotal = 0
        for i, item in enumerate(st.session_state.manual_invoice_items):
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            
            with col1:
                item['description'] = st.text_input(
                    f"Description {i+1}", 
                    value=item['description'], 
                    key=f"item_desc_{i}"
                )
            
            with col2:
                item['quantity'] = st.number_input(
                    f"Qty {i+1}", 
                    value=item['quantity'], 
                    min_value=0.0, 
                    step=0.1,
                    key=f"item_qty_{i}"
                )
            
            with col3:
                item['unit_price'] = st.number_input(
                    f"Unit Price {i+1}", 
                    value=item['unit_price'], 
                    min_value=0.0, 
                    step=0.01,
                    key=f"item_price_{i}"
                )
            
            with col4:
                line_total = item['quantity'] * item['unit_price']
                st.metric(f"Total {i+1}", f"${line_total:.2f}")
                total_subtotal += line_total
        
        # Add/remove item buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("+ Add Item"):
                st.session_state.manual_invoice_items.append({
                    "description": "", "quantity": 1.0, "unit_price": 0.0
                })
                st.rerun()
        
        with col2:
            if len(st.session_state.manual_invoice_items) > 1:
                if st.form_submit_button("- Remove Last Item"):
                    st.session_state.manual_invoice_items.pop()
                    st.rerun()
        
        # Invoice totals
        tax_amount = total_subtotal * (tax_rate / 100)
        total_amount = total_subtotal + tax_amount
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Subtotal", f"${total_subtotal:.2f}")
        with col2:
            st.metric("Tax", f"${tax_amount:.2f}")
        with col3:
            st.metric("Total", f"${total_amount:.2f}")
        
        # Notes
        notes = st.text_area("Invoice Notes", placeholder="Additional notes or payment instructions...")
        
        # Submit button
        submitted = st.form_submit_button("🧾 Create Invoice", type="primary")
        
        if submitted:
            if selected_customer_idx is not None and total_subtotal > 0:
                try:
                    customer = customers[selected_customer_idx]
                    
                    # Create invoice
                    invoice_data = {
                        'customer_id': customer['id'],
                        'job_id': None,  # Manual invoice
                        'due_date': due_date,
                        'subtotal': total_subtotal,
                        'tax_amount': tax_amount,
                        'total_amount': total_amount,
                        'notes': notes,
                        'created_by': st.session_state.user['id']
                    }
                    
                    invoice_id = create_invoice(invoice_data)
                    
                    if invoice_id:
                        # Add line items
                        for item in st.session_state.manual_invoice_items:
                            if item['description'] and item['quantity'] > 0:
                                add_invoice_item(
                                    invoice_id,
                                    item['description'],
                                    item['quantity'],
                                    item['unit_price']
                                )
                        
                        st.success(f"✅ Invoice created successfully! Invoice ID: {invoice_id}")
                        st.session_state.manual_invoice_items = [{"description": "", "quantity": 1.0, "unit_price": 0.0}]
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Failed to create invoice. Please try again.")
                
                except Exception as e:
                    st.error(f"Error creating invoice: {str(e)}")
            else:
                st.error("Please select a customer and add at least one item.")

def show_invoice_details():
    """Display detailed invoice view"""
    st.subheader("Invoice Details")
    
    # Invoice selection
    invoices = get_invoices()
    
    if not invoices:
        st.info("No invoices available.")
        return
    
    # Check if we have a selected invoice from session state
    selected_id = st.session_state.get('invoice_detail_id')
    
    if selected_id:
        # Find the invoice in our list
        selected_idx = None
        for i, inv in enumerate(invoices):
            if inv['id'] == selected_id:
                selected_idx = i
                break
    else:
        selected_idx = 0
    
    invoice_options = [f"{inv['invoice_number']} - {inv.get('first_name', '')} {inv.get('last_name', '')}" for inv in invoices]
    
    selected_invoice_idx = st.selectbox(
        "Select Invoice to View",
        range(len(invoice_options)),
        index=selected_idx if selected_idx is not None else 0,
        format_func=lambda x: invoice_options[x],
        key="invoice_detail_selector"
    )
    
    if selected_invoice_idx is not None:
        selected_invoice = invoices[selected_invoice_idx]
        invoice_details = get_invoice_details(selected_invoice['id'])
        
        if invoice_details:
            # Invoice header
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"## Invoice #{invoice_details['invoice_number']}")
                st.write(f"**Date:** {invoice_details['invoice_date']}")
                st.write(f"**Due Date:** {invoice_details['due_date']}")
                st.write(f"**Status:** {invoice_details['payment_status'].title()}")
            
            with col2:
                st.write(f"**Customer:** {invoice_details.get('first_name', '')} {invoice_details.get('last_name', '')}")
                st.write(f"**Email:** {invoice_details.get('email', 'N/A')}")
                st.write(f"**Phone:** {invoice_details.get('phone', 'N/A')}")
                if invoice_details.get('job_title'):
                    st.write(f"**Job:** {invoice_details['job_title']}")
            
            st.markdown("---")
            
            # Invoice items
            st.markdown("### Invoice Items")
            if invoice_details.get('items'):
                items_data = []
                for item in invoice_details['items']:
                    items_data.append({
                        "Description": item['description'],
                        "Quantity": f"{item['quantity']:g}",
                        "Unit Price": f"${item['unit_price']:.2f}",
                        "Total": f"${item['line_total']:.2f}"
                    })
                
                df = pd.DataFrame(items_data)
                st.table(df)
            else:
                st.info("No line items found for this invoice.")
            
            # Totals
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Subtotal", f"${invoice_details['subtotal']:.2f}")
            with col2:
                st.metric("Tax", f"${invoice_details.get('tax_amount', 0):.2f}")
            with col3:
                st.metric("Total", f"${invoice_details['total_amount']:.2f}")
            
            # Payment information
            st.markdown("### Payment Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Paid Amount", f"${invoice_details.get('paid_amount', 0):.2f}")
                outstanding = float(invoice_details['total_amount']) - float(invoice_details.get('paid_amount', 0))
                st.metric("Outstanding", f"${outstanding:.2f}")
            
            with col2:
                if invoice_details.get('payment_method'):
                    st.write(f"**Payment Method:** {invoice_details['payment_method']}")
                if invoice_details.get('payment_date'):
                    st.write(f"**Payment Date:** {invoice_details['payment_date']}")
            
            # Notes
            if invoice_details.get('notes'):
                st.markdown("### Notes")
                st.info(invoice_details['notes'])

def show_overdue_invoices():
    """Display overdue invoices"""
    st.subheader("⚠️ Overdue Invoices")
    
    overdue_invoices = get_overdue_invoices()
    
    if overdue_invoices:
        st.warning(f"You have {len(overdue_invoices)} overdue invoices requiring attention!")
        
        # Display overdue invoices
        overdue_data = []
        for invoice in overdue_invoices:
            customer_name = f"{invoice.get('first_name', '')} {invoice.get('last_name', '')}"
            days_overdue = (date.today() - invoice['due_date']).days
            
            overdue_data.append({
                "Invoice #": invoice['invoice_number'],
                "Customer": customer_name,
                "Amount Due": f"${float(invoice['total_amount']) - float(invoice.get('paid_amount', 0)):,.2f}",
                "Due Date": invoice['due_date'].strftime('%Y-%m-%d'),
                "Days Overdue": days_overdue,
                "Contact": invoice.get('email', 'No email'),
                "Phone": invoice.get('phone', 'No phone')
            })
        
        df = pd.DataFrame(overdue_data)
        st.dataframe(df, use_container_width=True)
        
        # Bulk actions
        st.markdown("#### Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Send All Reminders"):
                st.success(f"Reminder emails sent to {len(overdue_invoices)} customers! (Feature simulated)")
        
        with col2:
            if st.button("📞 Generate Call List"):
                st.info("Call list generated for overdue accounts.")
        
        with col3:
            if st.button("📊 Export Report"):
                st.success("Overdue report exported! (Feature simulated)")
    
    else:
        st.success("🎉 No overdue invoices! All payments are up to date.")

def show_payment_tracking():
    """Payment tracking and recording"""
    st.subheader("💳 Payment Tracking")
    
    # Quick payment recording
    st.markdown("#### Record Payment")
    
    # Get unpaid/partial invoices
    unpaid_invoices = get_invoices(status='unpaid') + get_invoices(status='partial')
    
    if unpaid_invoices:
        # Check if we have a selected invoice for payment from session state
        payment_id = st.session_state.get('payment_invoice_id')
        selected_idx = 0
        
        if payment_id:
            for i, inv in enumerate(unpaid_invoices):
                if inv['id'] == payment_id:
                    selected_idx = i
                    break
        
        invoice_options = [
            f"{inv['invoice_number']} - {inv.get('first_name', '')} {inv.get('last_name', '')} - ${float(inv['total_amount']) - float(inv.get('paid_amount', 0)):.2f}"
            for inv in unpaid_invoices
        ]
        
        selected_payment_idx = st.selectbox(
            "Select Invoice for Payment",
            range(len(invoice_options)),
            index=selected_idx,
            format_func=lambda x: invoice_options[x],
            key="payment_invoice_selector"
        )
        
        if selected_payment_idx is not None:
            selected_invoice = unpaid_invoices[selected_payment_idx]
            outstanding = float(selected_invoice['total_amount']) - float(selected_invoice.get('paid_amount', 0))
            
            with st.form("payment_form"):
                st.write(f"**Outstanding Amount:** ${outstanding:.2f}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    payment_amount = st.number_input(
                        "Payment Amount", 
                        min_value=0.0, 
                        max_value=float(outstanding),
                        value=float(outstanding),
                        step=0.01
                    )
                    payment_date = st.date_input("Payment Date", value=date.today())
                
                with col2:
                    payment_method = st.selectbox(
                        "Payment Method",
                        ["Check", "Credit Card", "Bank Transfer", "Cash", "Other"]
                    )
                    notes = st.text_area("Payment Notes", placeholder="Reference number, additional details...")
                
                submitted = st.form_submit_button("💰 Record Payment", type="primary")
                
                if submitted:
                    try:
                        new_paid_amount = float(selected_invoice.get('paid_amount', 0)) + payment_amount
                        
                        # Determine payment status
                        if new_paid_amount >= float(selected_invoice['total_amount']):
                            payment_status = 'paid'
                        elif new_paid_amount > 0:
                            payment_status = 'partial'
                        else:
                            payment_status = 'unpaid'
                        
                        payment_data = {
                            'paid_amount': new_paid_amount,
                            'payment_status': payment_status,
                            'payment_method': payment_method,
                            'payment_date': payment_date
                        }
                        
                        success = update_payment_status(selected_invoice['id'], payment_data)
                        
                        if success:
                            st.success(f"✅ Payment of ${payment_amount:.2f} recorded successfully!")
                            
                            # Add to financial records for payment collection
                            try:
                                from database import add_financial_record
                                from datetime import date
                                add_financial_record({
                                    'record_type': 'income',
                                    'amount': payment_amount,
                                    'description': f"Payment received for invoice {selected_invoice['invoice_number']}",
                                    'category': 'payment_collection',
                                    'job_id': selected_invoice.get('job_id'),
                                    'transaction_date': payment_date
                                })
                            except Exception as e:
                                st.warning(f"Payment recorded successfully, but failed to update financial records: {str(e)}")
                            
                            # Clear session state
                            if 'payment_invoice_id' in st.session_state:
                                del st.session_state.payment_invoice_id
                            
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Failed to record payment. Please try again.")
                    
                    except Exception as e:
                        st.error(f"Error recording payment: {str(e)}")
    
    else:
        st.success("🎉 All invoices are fully paid!")
    
    # Payment history summary
    st.markdown("---")
    st.markdown("#### Recent Payments")
    
    # Get recent payments (paid invoices from last 30 days)
    all_invoices = get_invoices()
    recent_payments = []
    
    for invoice in all_invoices:
        if (invoice.get('payment_date') and 
            invoice['payment_date'] >= (date.today() - timedelta(days=30))):
            recent_payments.append(invoice)
    
    if recent_payments:
        payment_data = []
        for payment in recent_payments[-10:]:  # Show last 10
            customer_name = f"{payment.get('first_name', '')} {payment.get('last_name', '')}"
            payment_data.append({
                "Date": payment['payment_date'].strftime('%Y-%m-%d'),
                "Invoice #": payment['invoice_number'],
                "Customer": customer_name,
                "Amount": f"${payment.get('paid_amount', 0):.2f}",
                "Method": payment.get('payment_method', 'N/A')
            })
        
        df = pd.DataFrame(payment_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent payments recorded.")

if __name__ == "__main__":
    show()