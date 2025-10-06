import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import sys
import mimetypes
import base64

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    upload_document, get_documents, get_document_by_id, update_document_metadata,
    archive_document, log_document_access, get_document_statistics,
    get_recent_document_activity, search_documents_by_content,
    get_customers, get_jobs
)

# Page configuration
REQUIRED_ROLE = 'admin'

def show():
    """Main document management page"""
    # Enforce role-based access control
    if not hasattr(st.session_state, 'user_role') or st.session_state.user_role not in ['admin', 'super_admin']:
        st.error("❌ Access denied. Document management requires admin privileges.")
        return
    
    st.title("📁 Document Management")
    
    # Document statistics overview
    show_document_stats()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 All Documents", 
        "📤 Upload Document", 
        "🔍 Search Documents",
        "📊 Analytics",
        "🔒 Access Log",
        "⚙️ Settings"
    ])
    
    with tab1:
        show_all_documents()
    
    with tab2:
        show_upload_document()
    
    with tab3:
        show_search_documents()
    
    with tab4:
        show_document_analytics()
    
    with tab5:
        show_access_log()
    
    with tab6:
        show_document_settings()

def show_document_stats():
    """Display document storage statistics dashboard"""
    stats = get_document_statistics()
    
    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Documents",
                stats.get('total_documents', 0)
            )
        
        with col2:
            st.metric(
                "Storage Used", 
                format_file_size(stats.get('total_storage_bytes', 0))
            )
        
        with col3:
            st.metric(
                "Customers with Docs",
                stats.get('customers_with_docs', 0)
            )
        
        with col4:
            st.metric(
                "Jobs with Docs",
                stats.get('jobs_with_docs', 0)
            )
        
        with col5:
            contracts = stats.get('contracts', 0)
            st.metric(
                "Contracts",
                contracts
            )
        
        # Document type breakdown
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Invoices", stats.get('invoice_docs', 0))
        with col2:
            st.metric("Photos", stats.get('photos', 0))
        with col3:
            st.metric("Plans", stats.get('plans', 0))
        with col4:
            st.metric("Other", stats.get('other_docs', 0))
    
    st.markdown("---")

def show_all_documents():
    """Display all documents with filtering and management"""
    st.subheader("Document Library")
    
    # Filters row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Customer filter
        customers = get_customers()
        customer_options = ["All Customers"] + [f"{c['first_name']} {c['last_name']}" for c in customers]
        customer_filter = st.selectbox("Filter by Customer", customer_options)
    
    with col2:
        # Document type filter
        doc_type_filter = st.selectbox(
            "Document Type",
            ["All", "contract", "invoice", "photo", "plan", "other"]
        )
    
    with col3:
        # Category filter
        category_filter = st.selectbox(
            "Category",
            ["All", "legal", "financial", "technical", "marketing", "other"]
        )
    
    with col4:
        # Quick search
        search_term = st.text_input("Quick Search", placeholder="Search filenames...")
    
    # Additional controls
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col2:
        show_archived = st.checkbox("Show Archived Documents")
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Name", "Size"])
    
    # Get filtered documents
    customer_id = None
    if customer_filter != "All Customers":
        for c in customers:
            if f"{c['first_name']} {c['last_name']}" == customer_filter:
                customer_id = c['id']
                break
    
    document_type = None if doc_type_filter == "All" else doc_type_filter
    category = None if category_filter == "All" else category_filter
    search = search_term if search_term else None
    
    try:
        documents = get_documents(
            customer_id=customer_id,
            document_type=document_type, 
            category=category,
            search=search,
            include_archived=show_archived
        )
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
        return
    
    if documents:
        # Create DataFrame for display
        doc_data = []
        for doc in documents:
            customer_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip() or "Unlinked"
            job_name = doc.get('job_title', 'N/A')
            
            # File type icon
            file_icon = get_file_type_icon(doc.get('mime_type', ''))
            
            doc_data.append({
                "📄": file_icon,
                "Filename": doc['original_filename'],
                "Type": doc['document_type'].title(),
                "Category": doc.get('category', 'N/A').title() if doc.get('category') else 'N/A',
                "Customer": customer_name,
                "Job": job_name,
                "Size": format_file_size(doc.get('file_size', 0)),
                "Uploaded": doc['created_at'].strftime('%Y-%m-%d') if doc['created_at'] else 'N/A',
                "Uploaded By": doc.get('uploaded_by_name', 'Unknown'),
                "ID": doc['id']
            })
        
        # Add numeric size for sorting
        for i, doc in enumerate(documents):
            doc_data[i]['_numeric_size'] = doc.get('file_size', 0)
        
        # Sort documents
        if sort_by == "Date (Oldest)":
            doc_data.sort(key=lambda x: x['Uploaded'])
        elif sort_by == "Name":
            doc_data.sort(key=lambda x: x['Filename'].lower())
        elif sort_by == "Size":
            doc_data.sort(key=lambda x: x['_numeric_size'], reverse=True)
        # Default: Date (Newest) - already sorted by database query
        
        df = pd.DataFrame(doc_data)
        
        # Display documents table
        st.dataframe(
            df.drop('ID', axis=1), 
            use_container_width=True,
            height=400
        )
        
        # Document actions
        st.subheader("Document Actions")
        
        if doc_data:
            # Document selection for actions
            selected_doc = st.selectbox(
                "Select Document for Actions",
                options=[f"{row['Filename']} ({row['Type']})" for row in doc_data],
                key="selected_doc_action"
            )
            
            # Find selected document ID
            selected_doc_id = None
            for row in doc_data:
                if f"{row['Filename']} ({row['Type']})" == selected_doc:
                    selected_doc_id = row['ID']
                    break
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("👁️ View Details"):
                    st.session_state.view_document_id = selected_doc_id
                    show_document_details(selected_doc_id)
            
            with col2:
                if st.button("📥 Download"):
                    handle_document_download(selected_doc_id)
            
            with col3:
                if st.button("✏️ Edit Metadata"):
                    st.session_state.edit_document_id = selected_doc_id
                    show_edit_document_form(selected_doc_id)
            
            with col4:
                if st.button("🗑️ Archive", type="secondary"):
                    if st.session_state.get('confirm_archive') == selected_doc_id:
                        # Perform archive with audit logging
                        try:
                            if archive_document(selected_doc_id, st.session_state.user['id']):
                                log_document_access(selected_doc_id, st.session_state.user['id'], 'archive')
                                st.success("Document archived successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to archive document.")
                        except Exception as e:
                            st.error(f"Archive failed: {str(e)}")
                    else:
                        st.session_state.confirm_archive = selected_doc_id
                        st.warning("Click again to confirm archive")
    
    else:
        st.info("No documents found matching your criteria.")
        if not documents:
            st.markdown("### 📤 Upload your first document")
            st.write("Get started by uploading contracts, photos, plans, or other project files.")

def show_upload_document():
    """Document upload interface"""
    st.subheader("Upload New Document")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose file to upload",
        type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'txt', 'csv'],
        help="Supported formats: PDF, Word, Excel, Images, Text files"
    )
    
    if uploaded_file is not None:
        # File details
        st.info(f"**File:** {uploaded_file.name} ({format_file_size(uploaded_file.size)})")
        
        # Upload form
        with st.form("upload_document_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Document type
                document_type = st.selectbox(
                    "Document Type *",
                    ["contract", "invoice", "photo", "plan", "other"],
                    format_func=lambda x: x.title()
                )
                
                # Category
                category = st.selectbox(
                    "Category",
                    ["", "legal", "financial", "technical", "marketing", "other"],
                    format_func=lambda x: x.title() if x else "Select Category"
                )
            
            with col2:
                # Customer association
                customers = get_customers()
                customer_options = ["No Customer"] + [f"{c['first_name']} {c['last_name']}" for c in customers]
                customer_selection = st.selectbox("Link to Customer", customer_options)
                
                # Job association
                jobs = get_jobs()
                job_options = ["No Job"] + [f"{job['job_title']} ({job['client_name']})" for job in jobs]
                job_selection = st.selectbox("Link to Job", job_options)
            
            # Description and tags
            description = st.text_area("Description", placeholder="Brief description of this document...")
            tags = st.text_input("Tags", placeholder="Comma-separated tags for easy searching")
            
            # Upload button
            submitted = st.form_submit_button("📤 Upload Document", type="primary")
            
            if submitted:
                try:
                    # Create uploads directory if it doesn't exist
                    os.makedirs("uploads", exist_ok=True)
                    
                    # Determine customer and job IDs
                    customer_id = None
                    if customer_selection != "No Customer":
                        for c in customers:
                            if f"{c['first_name']} {c['last_name']}" == customer_selection:
                                customer_id = c['id']
                                break
                    
                    job_id = None
                    if job_selection != "No Job":
                        for j in jobs:
                            if f"{j['job_title']} ({j['client_name']})" == job_selection:
                                job_id = j['id']
                                break
                    
                    # Prepare document data
                    document_data = {
                        'customer_id': customer_id,
                        'job_id': job_id,
                        'original_filename': uploaded_file.name,
                        'file_size': uploaded_file.size,
                        'mime_type': uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0],
                        'document_type': document_type,
                        'category': category if category else None,
                        'description': description if description else None,
                        'tags': tags if tags else None,
                        'uploaded_by': st.session_state.user['id']
                    }
                    
                    # Upload document
                    document_id = upload_document(document_data)
                    
                    if document_id:
                        # Save the actual file
                        doc = get_document_by_id(document_id)
                        if doc:
                            file_path = doc['file_path']
                            with open(file_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            
                            st.success(f"✅ Document uploaded successfully! Document ID: {document_id}")
                            st.balloons()
                            
                            # Show upload summary
                            st.markdown("#### Upload Summary")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Filename:** {uploaded_file.name}")
                                st.write(f"**Type:** {document_type.title()}")
                                st.write(f"**Size:** {format_file_size(uploaded_file.size)}")
                            with col2:
                                st.write(f"**Customer:** {customer_selection}")
                                st.write(f"**Job:** {job_selection}")
                                if category:
                                    st.write(f"**Category:** {category.title()}")
                            
                            st.rerun()
                        else:
                            st.error("Document record created but failed to retrieve details.")
                    else:
                        st.error("Failed to upload document. Please try again.")
                
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")

def show_search_documents():
    """Advanced document search interface"""
    st.subheader("🔍 Advanced Document Search")
    
    # Search form
    with st.form("search_form"):
        # Text search
        search_terms = st.text_input(
            "Search Terms", 
            placeholder="Enter keywords to search in filenames, descriptions, and tags"
        )
        
        # Advanced filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_range = st.date_input(
                "Date Range",
                value=[],
                help="Filter by upload date"
            )
        
        with col2:
            file_types = st.multiselect(
                "File Types",
                ["pdf", "doc", "docx", "jpg", "jpeg", "png", "xls", "xlsx", "txt"]
            )
        
        with col3:
            min_size = st.number_input("Min Size (KB)", min_value=0, value=0)
            max_size = st.number_input("Max Size (MB)", min_value=0, value=0)
        
        search_submitted = st.form_submit_button("🔍 Search", type="primary")
    
    # Perform search
    if search_submitted and search_terms:
        try:
            results = search_documents_by_content(search_terms)
            
            st.markdown(f"### Search Results ({len(results)} documents found)")
            
            if results:
                # Display search results with relevance scores
                for i, doc in enumerate(results[:20]):  # Show top 20 results
                    with st.expander(f"📄 {doc['original_filename']} (Score: {doc.get('relevance_score', 0):.2f})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Type:** {doc['document_type'].title()}")
                            st.write(f"**Size:** {format_file_size(doc.get('file_size', 0))}")
                            st.write(f"**Uploaded:** {doc['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                        with col2:
                            customer_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip()
                            st.write(f"**Customer:** {customer_name or 'Unlinked'}")
                            st.write(f"**Job:** {doc.get('job_title', 'N/A')}")
                            st.write(f"**Uploaded by:** {doc.get('uploaded_by_name', 'Unknown')}")
                        
                        if doc.get('description'):
                            st.write(f"**Description:** {doc['description']}")
                        
                        if doc.get('tags'):
                            st.write(f"**Tags:** {doc['tags']}")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"👁️ View", key=f"view_{doc['id']}"):
                                show_document_details(doc['id'])
                        with col2:
                            if st.button(f"📥 Download", key=f"download_{doc['id']}"):
                                handle_document_download(doc['id'])
                        with col3:
                            if st.button(f"✏️ Edit", key=f"edit_{doc['id']}"):
                                show_edit_document_form(doc['id'])
            else:
                st.info("No documents found matching your search terms.")
        
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
    
    elif search_submitted:
        st.warning("Please enter search terms to perform a search.")

def show_document_analytics():
    """Document analytics and insights"""
    st.subheader("📊 Document Analytics")
    
    # Get analytics data
    stats = get_document_statistics()
    recent_activity = get_recent_document_activity(20)
    
    # Storage analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Document Types Distribution")
        if stats:
            type_data = {
                'Contracts': stats.get('contracts', 0),
                'Invoices': stats.get('invoice_docs', 0),
                'Photos': stats.get('photos', 0),
                'Plans': stats.get('plans', 0),
                'Other': stats.get('other_docs', 0)
            }
            
            # Filter out zero values
            type_data = {k: v for k, v in type_data.items() if v > 0}
            
            if type_data:
                st.bar_chart(type_data)
            else:
                st.info("No documents to display")
    
    with col2:
        st.markdown("#### Storage Usage")
        if stats:
            total_bytes = stats.get('total_storage_bytes', 0)
            st.metric("Total Storage", format_file_size(total_bytes))
            
            # Storage by type (estimated)
            avg_size = total_bytes / max(stats.get('total_documents', 1), 1)
            storage_by_type = {
                'Contracts': stats.get('contracts', 0) * avg_size,
                'Invoices': stats.get('invoice_docs', 0) * avg_size,
                'Photos': stats.get('photos', 0) * avg_size,
                'Plans': stats.get('plans', 0) * avg_size,
                'Other': stats.get('other_docs', 0) * avg_size
            }
            
            storage_by_type = {k: format_file_size(v) for k, v in storage_by_type.items() if v > 0}
            
            for doc_type, size in storage_by_type.items():
                st.write(f"**{doc_type}:** {size}")
    
    # Recent activity
    st.markdown("#### Recent Document Activity")
    if recent_activity:
        activity_data = []
        for activity in recent_activity:
            customer_name = f"{activity.get('first_name', '')} {activity.get('last_name', '')}".strip()
            activity_data.append({
                "Time": activity['accessed_at'].strftime('%Y-%m-%d %H:%M'),
                "Action": activity['access_type'].title(),
                "Document": activity['original_filename'],
                "Type": activity['document_type'].title(),
                "User": activity.get('user_name', 'Unknown'),
                "Customer": customer_name or 'Unlinked'
            })
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True, height=300)
    else:
        st.info("No recent activity to display")

def show_access_log():
    """Document access logging and security"""
    st.subheader("🔒 Document Access Log")
    
    # Get recent access logs
    access_logs = get_recent_document_activity(50)
    
    if access_logs:
        # Access log filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            action_filter = st.selectbox(
                "Filter by Action",
                ["All"] + list(set(log['access_type'] for log in access_logs))
            )
        
        with col2:
            user_filter = st.selectbox(
                "Filter by User", 
                ["All"] + list(set(log.get('user_name', 'Unknown') for log in access_logs))
            )
        
        with col3:
            show_last_hours = st.selectbox("Show Last", [24, 48, 168, 720], format_func=lambda x: f"{x} hours")
        
        # Filter logs
        filtered_logs = access_logs
        if action_filter != "All":
            filtered_logs = [log for log in filtered_logs if log['access_type'] == action_filter]
        if user_filter != "All":
            filtered_logs = [log for log in filtered_logs if log.get('user_name') == user_filter]
        
        # Display access log
        log_data = []
        for log in filtered_logs:
            customer_name = f"{log.get('first_name', '')} {log.get('last_name', '')}".strip()
            
            # Add security indicators
            action_icon = {
                'upload': '📤',
                'download': '📥', 
                'view': '👁️',
                'edit': '✏️',
                'archive': '🗑️',
                'access': '🔍'
            }.get(log['access_type'], '📄')
            
            log_data.append({
                "🕒 Time": log['accessed_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "Action": f"{action_icon} {log['access_type'].title()}",
                "Document": log['original_filename'],
                "Type": log['document_type'].title(),
                "User": log.get('user_name', 'Unknown'),
                "Customer": customer_name or 'Unlinked',
                "IP": log.get('ip_address', 'N/A')
            })
        
        df = pd.DataFrame(log_data)
        st.dataframe(df, use_container_width=True, height=400)
        
        # Security summary
        st.markdown("#### Security Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_access = len(filtered_logs)
            st.metric("Total Access Events", total_access)
        
        with col2:
            unique_users = len(set(log.get('user_name', 'Unknown') for log in filtered_logs))
            st.metric("Unique Users", unique_users)
        
        with col3:
            unique_docs = len(set(log['original_filename'] for log in filtered_logs))
            st.metric("Documents Accessed", unique_docs)
        
        with col4:
            download_count = sum(1 for log in filtered_logs if log['access_type'] == 'download')
            st.metric("Downloads", download_count)
    
    else:
        st.info("No access log entries found.")

def show_document_settings():
    """Document management settings and utilities"""
    st.subheader("⚙️ Document Settings & Utilities")
    
    # Storage management
    st.markdown("#### Storage Management")
    
    stats = get_document_statistics()
    if stats:
        total_storage = stats.get('total_storage_bytes', 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Storage Used", format_file_size(total_storage))
        with col2:
            storage_limit = 1024 * 1024 * 1024  # 1GB limit for demo
            usage_percent = (total_storage / storage_limit) * 100 if storage_limit > 0 else 0
            st.metric("Storage Usage", f"{usage_percent:.1f}%")
    
    st.markdown("---")
    
    # Cleanup utilities
    st.markdown("#### Cleanup Utilities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clean Archived Documents"):
            st.info("This would permanently delete archived documents older than 30 days. (Feature simulated)")
    
    with col2:
        if st.button("🔍 Check Orphaned Files"):
            st.info("This would scan for files without database records. (Feature simulated)")
    
    st.markdown("---")
    
    # Backup and export
    st.markdown("#### Backup & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Export Document List"):
            # Create CSV export of documents
            documents = get_documents()
            if documents:
                doc_data = []
                for doc in documents:
                    customer_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip()
                    doc_data.append({
                        'Filename': doc['original_filename'],
                        'Type': doc['document_type'],
                        'Category': doc.get('category', ''),
                        'Customer': customer_name or 'Unlinked',
                        'Job': doc.get('job_title', ''),
                        'Size': doc.get('file_size', 0),
                        'Uploaded': doc['created_at'].strftime('%Y-%m-%d %H:%M:%S') if doc['created_at'] else '',
                        'Description': doc.get('description', ''),
                        'Tags': doc.get('tags', '')
                    })
                
                df = pd.DataFrame(doc_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Document List CSV",
                    data=csv,
                    file_name=f"documents_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No documents to export")
    
    with col2:
        if st.button("🗂️ Generate Storage Report"):
            st.info("This would generate a detailed storage usage report. (Feature simulated)")

def show_document_details(document_id):
    """Show detailed view of a specific document"""
    # Check access permissions
    if not hasattr(st.session_state, 'user') or not st.session_state.user:
        st.error("Access denied. Please log in.")
        return
    
    doc = get_document_by_id(document_id)
    
    if doc:
        # Log the view access with enhanced tracking
        try:
            log_document_access(document_id, st.session_state.user['id'], 'view')
        except Exception as e:
            st.warning(f"Failed to log document access: {str(e)}")
        
        st.markdown("### 📄 Document Details")
        
        # Document header
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Filename:** {doc['original_filename']}")
            st.write(f"**Type:** {doc['document_type'].title()}")
            st.write(f"**Category:** {doc.get('category', 'N/A').title() if doc.get('category') else 'N/A'}")
            st.write(f"**Size:** {format_file_size(doc.get('file_size', 0))}")
        
        with col2:
            customer_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip()
            st.write(f"**Customer:** {customer_name or 'Unlinked'}")
            st.write(f"**Job:** {doc.get('job_title', 'N/A')}")
            st.write(f"**Uploaded by:** {doc.get('uploaded_by_name', 'Unknown')}")
            st.write(f"**Upload Date:** {doc['created_at'].strftime('%Y-%m-%d %H:%M')}")
        
        if doc.get('description'):
            st.write(f"**Description:** {doc['description']}")
        
        if doc.get('tags'):
            st.write(f"**Tags:** {doc['tags']}")
        
        # Document actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download", key=f"download_detail_{document_id}"):
                handle_document_download(document_id)
        
        with col2:
            if st.button("✏️ Edit Metadata", key=f"edit_detail_{document_id}"):
                show_edit_document_form(document_id)
        
        with col3:
            if st.button("🗑️ Archive", key=f"archive_detail_{document_id}"):
                if archive_document(document_id, st.session_state.user['id']):
                    st.success("Document archived successfully!")
                    st.rerun()
                else:
                    st.error("Failed to archive document.")
    
    else:
        st.error("Document not found or access denied.")

def show_edit_document_form(document_id):
    """Show form to edit document metadata"""
    # Check access permissions
    if not hasattr(st.session_state, 'user') or not st.session_state.user:
        st.error("Access denied. Please log in.")
        return
    
    doc = get_document_by_id(document_id)
    
    if doc:
        st.markdown("### ✏️ Edit Document Metadata")
        
        with st.form(f"edit_doc_form_{document_id}"):
            # Current values as defaults
            description = st.text_area("Description", value=doc.get('description', ''))
            
            # Category
            current_category = doc.get('category', '')
            category_options = ["", "legal", "financial", "technical", "marketing", "other"]
            current_idx = category_options.index(current_category) if current_category in category_options else 0
            
            category = st.selectbox(
                "Category",
                category_options,
                index=current_idx,
                format_func=lambda x: x.title() if x else "Select Category"
            )
            
            # Tags
            tags = st.text_input("Tags", value=doc.get('tags', ''))
            
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
            
            if submitted:
                update_data = {
                    'description': description if description else None,
                    'category': category if category else None,
                    'tags': tags if tags else None
                }
                
                if update_document_metadata(document_id, update_data):
                    # Log the edit action
                    try:
                        log_document_access(document_id, st.session_state.user['id'], 'edit')
                    except Exception as e:
                        st.warning(f"Failed to log document access: {str(e)}")
                    
                    st.success("Document metadata updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update document metadata.")
    
    else:
        st.error("Document not found or access denied.")

def handle_document_download(document_id):
    """Handle document download"""
    # Check access permissions
    if not hasattr(st.session_state, 'user') or not st.session_state.user:
        st.error("Access denied. Please log in.")
        return
    
    doc = get_document_by_id(document_id)
    
    if doc and os.path.exists(doc['file_path']):
        try:
            # Log the download with enhanced tracking
            log_document_access(document_id, st.session_state.user['id'], 'download')
            
            # Read file and create download
            with open(doc['file_path'], 'rb') as f:
                file_data = f.read()
            
            st.download_button(
                label=f"📥 Download {doc['original_filename']}",
                data=file_data,
                file_name=doc['original_filename'],
                mime=doc.get('mime_type', 'application/octet-stream'),
                key=f"download_btn_{document_id}"
            )
            
        except Exception as e:
            st.error(f"Download failed: {str(e)}")
    else:
        st.error("Document file not found or access denied.")

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if not size_bytes:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def get_file_type_icon(mime_type):
    """Get appropriate icon for file type"""
    if not mime_type:
        return "📄"
    
    if mime_type.startswith('image/'):
        return "🖼️"
    elif 'pdf' in mime_type:
        return "📕"
    elif any(word in mime_type for word in ['word', 'document']):
        return "📘"
    elif any(word in mime_type for word in ['excel', 'spreadsheet']):
        return "📊"
    elif 'text' in mime_type:
        return "📝"
    else:
        return "📄"

if __name__ == "__main__":
    show()