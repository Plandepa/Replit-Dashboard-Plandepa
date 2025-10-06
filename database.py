import psycopg2
import psycopg2.extras
import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters from environment
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'database': os.getenv('PGDATABASE', 'postgres'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'port': os.getenv('PGPORT', '5432')
}

def get_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def init_database():
    """Initialize database - tables already created in Supabase"""
    return True

def execute_query(query, params=None, fetch=False):
    """Execute database query"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        
        # Determine if this is a write operation that needs to be committed
        is_write_operation = query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'))
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount
        
        # Commit all write operations, regardless of fetch parameter
        if is_write_operation:
            conn.commit()
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        st.error(f"Database query error: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return None

def get_user_by_username(username):
    """Get user by username"""
    query = "SELECT * FROM users WHERE username = %s"
    result = execute_query(query, (username,), fetch=True)
    return result[0] if result else None

def create_estimate(data):
    """Create new estimate"""
    # If no customer_id provided, try to find or create customer
    if not data.get('customer_id') and data.get('client_name'):
        customer_id = find_or_create_customer_from_estimate(data)
        data['customer_id'] = customer_id
    
    query = """
        INSERT INTO estimates (customer_id, client_name, client_email, client_phone, project_title, 
                             description, estimated_cost, created_by)
        VALUES (%(customer_id)s, %(client_name)s, %(client_email)s, %(client_phone)s, %(project_title)s,
                %(description)s, %(estimated_cost)s, %(created_by)s)
        RETURNING id
    """
    result = execute_query(query, data, fetch=True)
    return result[0]['id'] if result else None

def get_estimates(status=None):
    """Get estimates with optional status filter"""
    query = "SELECT * FROM estimates"
    params = None
    if status:
        query += " WHERE status = %s"
        params = (status,)
    query += " ORDER BY created_at DESC"
    return execute_query(query, params, fetch=True) or []

def update_estimate_status(estimate_id, status):
    """Update estimate status"""
    query = "UPDATE estimates SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
    return execute_query(query, (status, estimate_id))

def create_job_from_estimate(estimate_id, job_data):
    """Create job from approved estimate"""
    query = """
        INSERT INTO jobs (estimate_id, job_title, client_name, start_date, 
                         actual_cost, assigned_crew, notes)
        VALUES (%(estimate_id)s, %(job_title)s, %(client_name)s, %(start_date)s,
                %(actual_cost)s, %(assigned_crew)s, %(notes)s)
        RETURNING id
    """
    job_data['estimate_id'] = estimate_id
    result = execute_query(query, job_data, fetch=True)
    return result[0]['id'] if result else None

def get_jobs(status=None):
    """Get jobs with optional status filter"""
    query = """
        SELECT j.*, e.project_title as estimate_title, e.customer_id
        FROM jobs j
        LEFT JOIN estimates e ON j.estimate_id = e.id
    """
    params = None
    if status:
        query += " WHERE j.status = %s"
        params = (status,)
    query += " ORDER BY j.created_at DESC"
    return execute_query(query, params, fetch=True) or []

def get_job_details(job_id):
    """Get job details by ID"""
    query = """
        SELECT j.*, e.project_title as estimate_title, e.customer_id
        FROM jobs j
        LEFT JOIN estimates e ON j.estimate_id = e.id
        WHERE j.id = %s
    """
    result = execute_query(query, (job_id,), fetch=True)
    return result[0] if result else None

def log_ai_call(call_data):
    """Log AI caller activity"""
    query = """
        INSERT INTO ai_calls (call_type, phone_number, client_name, call_duration,
                             call_status, call_summary, follow_up_required)
        VALUES (%(call_type)s, %(phone_number)s, %(client_name)s, %(call_duration)s,
                %(call_status)s, %(call_summary)s, %(follow_up_required)s)
        RETURNING id
    """
    result = execute_query(query, call_data, fetch=True)
    return result[0]['id'] if result else None

def get_ai_calls(limit=50):
    """Get recent AI calls"""
    query = "SELECT * FROM ai_calls ORDER BY created_at DESC LIMIT %s"
    return execute_query(query, (limit,), fetch=True) or []

def add_financial_record(record_data):
    """Add financial record"""
    query = """
        INSERT INTO financial_records (record_type, amount, description, category, job_id, transaction_date)
        VALUES (%(record_type)s, %(amount)s, %(description)s, %(category)s, %(job_id)s, %(transaction_date)s)
        RETURNING id
    """
    result = execute_query(query, record_data, fetch=True)
    return result[0]['id'] if result else None

def get_financial_summary():
    """Get financial summary data"""
    query = """
        SELECT 
            record_type,
            SUM(amount) as total_amount,
            COUNT(*) as count
        FROM financial_records 
        GROUP BY record_type
    """
    return execute_query(query, fetch=True) or []

def get_monthly_revenue():
    """Get monthly revenue data"""
    query = """
        SELECT 
            DATE_TRUNC('month', transaction_date) as month,
            SUM(CASE WHEN record_type = 'income' THEN amount ELSE 0 END) as revenue,
            SUM(CASE WHEN record_type = 'expense' THEN amount ELSE 0 END) as expenses
        FROM financial_records 
        WHERE transaction_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', transaction_date)
        ORDER BY month
    """
    return execute_query(query, fetch=True) or []

# Customer Management Functions

def create_customer(customer_data):
    """Create new customer"""
    query = """
        INSERT INTO customers (first_name, last_name, email, phone, address, city, state, 
                             zip_code, company_name, customer_type, lead_source, notes)
        VALUES (%(first_name)s, %(last_name)s, %(email)s, %(phone)s, %(address)s, %(city)s, 
                %(state)s, %(zip_code)s, %(company_name)s, %(customer_type)s, %(lead_source)s, %(notes)s)
        RETURNING id
    """
    result = execute_query(query, customer_data, fetch=True)
    return result[0]['id'] if result else None

def get_customers(status=None, search=None):
    """Get customers with optional filtering"""
    query = "SELECT * FROM customers"
    params = []
    conditions = []
    
    if status:
        conditions.append("status = %s")
        params.append(status)
    
    if search:
        conditions.append("(first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR company_name ILIKE %s)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term, search_term])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC"
    return execute_query(query, params, fetch=True) or []

def get_customer_by_id(customer_id):
    """Get customer by ID"""
    query = "SELECT * FROM customers WHERE id = %s"
    result = execute_query(query, (customer_id,), fetch=True)
    return result[0] if result else None

def update_customer(customer_id, customer_data):
    """Update customer information"""
    query = """
        UPDATE customers SET 
            first_name = %(first_name)s, last_name = %(last_name)s, email = %(email)s, 
            phone = %(phone)s, address = %(address)s, city = %(city)s, state = %(state)s,
            zip_code = %(zip_code)s, company_name = %(company_name)s, customer_type = %(customer_type)s,
            lead_source = %(lead_source)s, status = %(status)s, notes = %(notes)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %(customer_id)s
    """
    customer_data['customer_id'] = customer_id
    return execute_query(query, customer_data)

def delete_customer(customer_id):
    """Delete customer (soft delete by setting status to inactive)"""
    query = "UPDATE customers SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE id = %s"
    return execute_query(query, (customer_id,))

# Customer Contact History Functions

def add_customer_contact(contact_data):
    """Add customer contact/interaction record"""
    query = """
        INSERT INTO customer_contacts (customer_id, contact_type, subject, description, 
                                     contact_date, follow_up_date, created_by)
        VALUES (%(customer_id)s, %(contact_type)s, %(subject)s, %(description)s,
                %(contact_date)s, %(follow_up_date)s, %(created_by)s)
        RETURNING id
    """
    result = execute_query(query, contact_data, fetch=True)
    return result[0]['id'] if result else None

def get_customer_contacts(customer_id, limit=50):
    """Get contact history for a customer"""
    query = """
        SELECT cc.*, u.full_name as created_by_name
        FROM customer_contacts cc
        LEFT JOIN users u ON cc.created_by = u.id
        WHERE cc.customer_id = %s
        ORDER BY cc.contact_date DESC
        LIMIT %s
    """
    return execute_query(query, (customer_id, limit), fetch=True) or []

def update_contact_completed(contact_id, completed=True):
    """Mark a contact/follow-up as completed"""
    query = "UPDATE customer_contacts SET completed = %s WHERE id = %s"
    return execute_query(query, (completed, contact_id))

def get_pending_follow_ups():
    """Get all pending follow-ups across all customers"""
    query = """
        SELECT cc.*, c.first_name, c.last_name, c.company_name, u.full_name as created_by_name
        FROM customer_contacts cc
        JOIN customers c ON cc.customer_id = c.id
        LEFT JOIN users u ON cc.created_by = u.id
        WHERE cc.follow_up_date IS NOT NULL 
        AND cc.follow_up_date <= CURRENT_DATE 
        AND cc.completed = FALSE
        ORDER BY cc.follow_up_date ASC
    """
    return execute_query(query, fetch=True) or []

# Helper functions for customer integration

def find_or_create_customer_from_estimate(estimate_data):
    """Find existing customer or create new one from estimate data"""
    # Try to find existing customer by email or phone
    if estimate_data.get('client_email'):
        existing = execute_query(
            "SELECT id FROM customers WHERE email = %s LIMIT 1", 
            (estimate_data['client_email'],), 
            fetch=True
        )
        if existing:
            return existing[0]['id']
    
    # Create new customer from estimate data
    names = estimate_data['client_name'].split(' ', 1)
    customer_data = {
        'first_name': names[0],
        'last_name': names[1] if len(names) > 1 else '',
        'email': estimate_data.get('client_email'),
        'phone': estimate_data.get('client_phone'),
        'address': None,
        'city': None,
        'state': None,
        'zip_code': None,
        'company_name': None,
        'customer_type': 'residential',
        'lead_source': 'estimate_request',
        'notes': f"Created from estimate request for: {estimate_data.get('project_title', 'Unknown project')}"
    }
    
    return create_customer(customer_data)

def get_customer_projects_summary(customer_id):
    """Get summary of all projects/jobs for a customer"""
    query = """
        SELECT 
            COUNT(e.id) as total_estimates,
            COUNT(CASE WHEN e.status = 'approved' THEN 1 END) as approved_estimates,
            COUNT(j.id) as total_jobs,
            COUNT(CASE WHEN j.status = 'completed' THEN 1 END) as completed_jobs,
            COALESCE(SUM(j.actual_cost), 0) as total_revenue
        FROM customers c
        LEFT JOIN estimates e ON c.id = e.customer_id
        LEFT JOIN jobs j ON e.id = j.estimate_id
        WHERE c.id = %s
        GROUP BY c.id
    """
    result = execute_query(query, (customer_id,), fetch=True)
    return result[0] if result else {
        'total_estimates': 0, 'approved_estimates': 0, 'total_jobs': 0, 
        'completed_jobs': 0, 'total_revenue': 0
    }

# Invoice Management Functions

def generate_invoice_number():
    """Generate unique invoice number"""
    import random
    import string
    from datetime import datetime
    
    # Format: INV-YYYY-XXXX where X is random
    year = datetime.now().year
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"INV-{year}-{suffix}"

def create_invoice(data):
    """Create new invoice from job data"""
    # Generate invoice number if not provided
    if 'invoice_number' not in data:
        data['invoice_number'] = generate_invoice_number()
    
    # Calculate due date (30 days from invoice date)
    from datetime import datetime, timedelta
    if 'due_date' not in data:
        due_date = datetime.now().date() + timedelta(days=30)
        data['due_date'] = due_date
    
    query = """
        INSERT INTO invoices (customer_id, job_id, invoice_number, due_date, 
                            subtotal, tax_amount, total_amount, created_by)
        VALUES (%(customer_id)s, %(job_id)s, %(invoice_number)s, %(due_date)s,
                %(subtotal)s, %(tax_amount)s, %(total_amount)s, %(created_by)s)
        RETURNING id
    """
    result = execute_query(query, data, fetch=True)
    return result[0]['id'] if result else None

def add_invoice_item(invoice_id, description, quantity, unit_price):
    """Add line item to invoice"""
    line_total = float(quantity) * float(unit_price)
    query = """
        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, line_total)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    result = execute_query(query, (invoice_id, description, quantity, unit_price, line_total), fetch=True)
    
    # Update invoice totals
    update_invoice_totals(invoice_id)
    return result[0]['id'] if result else None

def update_invoice_totals(invoice_id):
    """Recalculate invoice totals based on line items"""
    query = """
        UPDATE invoices 
        SET subtotal = (
            SELECT COALESCE(SUM(line_total), 0) 
            FROM invoice_items 
            WHERE invoice_id = %s
        ),
        total_amount = subtotal + tax_amount,
        updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    return execute_query(query, (invoice_id, invoice_id))

def get_invoices(status=None, customer_id=None):
    """Get invoices with optional filters"""
    query = """
        SELECT i.*, c.first_name, c.last_name, j.job_title
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        LEFT JOIN jobs j ON i.job_id = j.id
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND i.payment_status = %s"
        params.append(status)
    
    if customer_id:
        query += " AND i.customer_id = %s"
        params.append(customer_id)
    
    query += " ORDER BY i.created_at DESC"
    return execute_query(query, params, fetch=True) or []

def get_invoice_details(invoice_id):
    """Get invoice with line items"""
    invoice_query = """
        SELECT i.*, c.first_name, c.last_name, c.email, c.phone, c.address, 
               c.city, c.state, c.zip_code, j.job_title
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        LEFT JOIN jobs j ON i.job_id = j.id
        WHERE i.id = %s
    """
    items_query = """
        SELECT * FROM invoice_items 
        WHERE invoice_id = %s 
        ORDER BY id
    """
    
    invoice = execute_query(invoice_query, (invoice_id,), fetch=True)
    items = execute_query(items_query, (invoice_id,), fetch=True)
    
    if invoice:
        invoice[0]['items'] = items or []
        return invoice[0]
    return None

def update_payment_status(invoice_id, payment_data):
    """Update invoice payment status"""
    query = """
        UPDATE invoices 
        SET paid_amount = %(paid_amount)s,
            payment_status = %(payment_status)s,
            payment_method = %(payment_method)s,
            payment_date = %(payment_date)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %(invoice_id)s
    """
    payment_data['invoice_id'] = invoice_id
    return execute_query(query, payment_data)

def generate_invoice_from_job(job_id, created_by):
    """Automatically generate invoice from completed job"""
    # Get job details
    job = get_job_details(job_id)
    if not job or job['status'] != 'completed':
        return None
    
    # Calculate invoice amounts
    subtotal = float(job['actual_cost']) if job['actual_cost'] else 0
    tax_rate = 0.08  # 8% tax rate
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    
    # Create invoice
    invoice_data = {
        'customer_id': job.get('customer_id'),
        'job_id': job_id,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'created_by': created_by
    }
    
    invoice_id = create_invoice(invoice_data)
    
    if invoice_id:
        # Add main job as line item
        add_invoice_item(invoice_id, job['job_title'], 1, subtotal)
        
        # Update financial records
        try:
            add_financial_record({
                'record_type': 'income',
                'amount': total_amount,
                'description': f"Invoice generated for job: {job['job_title']}",
                'category': 'invoice_generation',
                'job_id': job_id,
                'transaction_date': datetime.now().date()
            })
        except Exception as e:
            # Don't let financial record failure break invoice creation
            print(f"Warning: Failed to create financial record: {e}")
    
    return invoice_id

def get_overdue_invoices():
    """Get all overdue invoices"""
    from datetime import datetime
    query = """
        SELECT i.*, c.first_name, c.last_name, c.email, c.phone
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.payment_status IN ('unpaid', 'partial')
        AND i.due_date < CURRENT_DATE
        ORDER BY i.due_date ASC
    """
    return execute_query(query, fetch=True) or []

def get_invoice_statistics():
    """Get invoice summary statistics"""
    query = """
        SELECT 
            COUNT(*) as total_invoices,
            COUNT(CASE WHEN payment_status = 'paid' THEN 1 END) as paid_invoices,
            COUNT(CASE WHEN payment_status = 'unpaid' THEN 1 END) as unpaid_invoices,
            COUNT(CASE WHEN payment_status = 'partial' THEN 1 END) as partial_invoices,
            COUNT(CASE WHEN due_date < CURRENT_DATE AND payment_status IN ('unpaid', 'partial') THEN 1 END) as overdue_invoices,
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(paid_amount), 0) as total_collected,
            COALESCE(SUM(total_amount - paid_amount), 0) as outstanding_amount
        FROM invoices
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else {}

# Document Management Functions

def upload_document(document_data):
    """Upload and store document metadata"""
    import uuid
    import os
    from datetime import datetime
    
    # Generate unique filename to prevent conflicts
    file_extension = os.path.splitext(document_data['original_filename'])[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create document record
    doc_record = {
        'customer_id': document_data.get('customer_id'),
        'job_id': document_data.get('job_id'),
        'filename': unique_filename,
        'original_filename': document_data['original_filename'],
        'file_path': os.path.join('uploads', unique_filename),
        'file_size': document_data.get('file_size'),
        'mime_type': document_data.get('mime_type'),
        'document_type': document_data['document_type'],
        'category': document_data.get('category'),
        'description': document_data.get('description'),
        'tags': document_data.get('tags'),
        'uploaded_by': document_data['uploaded_by']
    }
    
    query = """
        INSERT INTO documents (customer_id, job_id, filename, original_filename, file_path, 
                             file_size, mime_type, document_type, category, description, 
                             tags, uploaded_by)
        VALUES (%(customer_id)s, %(job_id)s, %(filename)s, %(original_filename)s, %(file_path)s,
                %(file_size)s, %(mime_type)s, %(document_type)s, %(category)s, %(description)s,
                %(tags)s, %(uploaded_by)s)
        RETURNING id
    """
    
    result = execute_query(query, doc_record, fetch=True)
    if result:
        document_id = result[0]['id']
        # Log the upload action
        log_document_access(document_id, document_data['uploaded_by'], 'upload')
        return document_id
    return None

def get_documents(customer_id=None, job_id=None, document_type=None, category=None, search=None, include_archived=False):
    """Get documents with optional filtering"""
    query = """
        SELECT d.*, c.first_name, c.last_name, j.job_title, u.full_name as uploaded_by_name
        FROM documents d
        LEFT JOIN customers c ON d.customer_id = c.id
        LEFT JOIN jobs j ON d.job_id = j.id
        LEFT JOIN users u ON d.uploaded_by = u.id
        WHERE 1=1
    """
    params = []
    
    # Filter by active/archived status
    if not include_archived:
        query += " AND d.is_active = TRUE"
    else:
        query += " AND d.is_active = FALSE"
    if customer_id:
        query += " AND d.customer_id = %s"
        params.append(customer_id)
    
    if job_id:
        query += " AND d.job_id = %s"
        params.append(job_id)
    
    if document_type:
        query += " AND d.document_type = %s"
        params.append(document_type)
    
    if category:
        query += " AND d.category = %s"
        params.append(category)
    
    if search:
        query += " AND (d.original_filename ILIKE %s OR d.description ILIKE %s OR d.tags ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY d.created_at DESC"
    return execute_query(query, params, fetch=True) or []

def get_document_by_id(document_id):
    """Get document details by ID"""
    query = """
        SELECT d.*, c.first_name, c.last_name, j.job_title, u.full_name as uploaded_by_name
        FROM documents d
        LEFT JOIN customers c ON d.customer_id = c.id
        LEFT JOIN jobs j ON d.job_id = j.id
        LEFT JOIN users u ON d.uploaded_by = u.id
        WHERE d.id = %s AND d.is_active = TRUE
    """
    result = execute_query(query, (document_id,), fetch=True)
    return result[0] if result else None

def update_document_metadata(document_id, update_data):
    """Update document metadata"""
    query = """
        UPDATE documents 
        SET description = %(description)s, 
            category = %(category)s,
            tags = %(tags)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %(document_id)s AND is_active = TRUE
    """
    update_data['document_id'] = document_id
    return execute_query(query, update_data)

def archive_document(document_id, user_id):
    """Archive document (soft delete)"""
    query = "UPDATE documents SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
    success = execute_query(query, (document_id,))
    
    if success:
        log_document_access(document_id, user_id, 'archive')
    
    return success

def log_document_access(document_id, user_id, access_type, ip_address=None, user_agent=None):
    """Log document access for security tracking"""
    query = """
        INSERT INTO document_access_log (document_id, user_id, access_type, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(query, (document_id, user_id, access_type, ip_address, user_agent))

def get_document_statistics():
    """Get document storage statistics"""
    query = """
        SELECT 
            COUNT(*) as total_documents,
            COUNT(CASE WHEN document_type = 'contract' THEN 1 END) as contracts,
            COUNT(CASE WHEN document_type = 'invoice' THEN 1 END) as invoice_docs,
            COUNT(CASE WHEN document_type = 'photo' THEN 1 END) as photos,
            COUNT(CASE WHEN document_type = 'plan' THEN 1 END) as plans,
            COUNT(CASE WHEN document_type = 'other' THEN 1 END) as other_docs,
            COALESCE(SUM(file_size), 0) as total_storage_bytes,
            COUNT(DISTINCT customer_id) as customers_with_docs,
            COUNT(DISTINCT job_id) as jobs_with_docs
        FROM documents
        WHERE is_active = TRUE
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else {}

def get_recent_document_activity(limit=10):
    """Get recent document access activity"""
    query = """
        SELECT dal.*, d.original_filename, d.document_type, u.full_name as user_name,
               c.first_name, c.last_name
        FROM document_access_log dal
        JOIN documents d ON dal.document_id = d.id
        JOIN users u ON dal.user_id = u.id
        LEFT JOIN customers c ON d.customer_id = c.id
        WHERE d.is_active = TRUE
        ORDER BY dal.accessed_at DESC
        LIMIT %s
    """
    return execute_query(query, (limit,), fetch=True) or []

def search_documents_by_content(search_terms):
    """Search documents by filename, description, and tags"""
    query = """
        SELECT d.*, c.first_name, c.last_name, j.job_title, u.full_name as uploaded_by_name,
               ts_rank(to_tsvector('english', d.original_filename || ' ' || COALESCE(d.description, '') || ' ' || COALESCE(d.tags, '')), 
                       plainto_tsquery('english', %s)) as relevance_score
        FROM documents d
        LEFT JOIN customers c ON d.customer_id = c.id
        LEFT JOIN jobs j ON d.job_id = j.id
        LEFT JOIN users u ON d.uploaded_by = u.id
        WHERE d.is_active = TRUE
        AND to_tsvector('english', d.original_filename || ' ' || COALESCE(d.description, '') || ' ' || COALESCE(d.tags, ''))
        @@ plainto_tsquery('english', %s)
        ORDER BY relevance_score DESC, d.created_at DESC
        LIMIT 50
    """
    return execute_query(query, (search_terms, search_terms), fetch=True) or []

# Enhanced AI Caller Analytics Functions

def get_calls_by_date_range(start_date, end_date):
    """Get AI calls within a specific date range"""
    query = """
        SELECT * FROM ai_calls 
        WHERE created_at >= %s AND created_at <= %s
        ORDER BY created_at DESC
    """
    end_date_with_time = f"{end_date} 23:59:59"
    return execute_query(query, (start_date, end_date_with_time), fetch=True) or []

def get_conversion_metrics(start_date, end_date):
    """Calculate conversion rates from calls to estimates to jobs using single cohort"""
    try:
        end_date_with_time = f"{end_date} 23:59:59"
        
        # Get total calls in date range
        calls_query = """
            SELECT COUNT(*) as total_calls,
                   COUNT(CASE WHEN call_status = 'completed' THEN 1 END) as completed_calls
            FROM ai_calls 
            WHERE created_at >= %s AND created_at <= %s
        """
        
        # Single cohort query: calls → estimates → jobs
        conversion_query = """
            SELECT 
                COUNT(DISTINCT ac.id) AS total_calls_in_funnel,
                COUNT(DISTINCT CASE WHEN e.id IS NOT NULL THEN ac.id END) AS calls_with_estimates,
                COUNT(DISTINCT e.id) AS estimates_from_calls,
                COUNT(DISTINCT j.id) AS jobs_from_call_estimates
            FROM ai_calls ac
            LEFT JOIN estimates e ON e.client_phone = ac.phone_number
                                  AND e.created_at BETWEEN ac.created_at AND ac.created_at + INTERVAL '30 days'
            LEFT JOIN jobs j ON j.estimate_id = e.id
                             AND j.created_at BETWEEN e.created_at AND e.created_at + INTERVAL '60 days'
            WHERE ac.created_at >= %s AND ac.created_at <= %s
        """
        
        call_stats = execute_query(calls_query, (start_date, end_date_with_time), fetch=True)
        conversion_stats = execute_query(conversion_query, (start_date, end_date_with_time), fetch=True)
        
        if call_stats and conversion_stats:
            total_calls = call_stats[0]['total_calls'] or 0
            calls_with_estimates = conversion_stats[0]['calls_with_estimates'] or 0
            estimates_from_calls = conversion_stats[0]['estimates_from_calls'] or 0
            jobs_from_call_estimates = conversion_stats[0]['jobs_from_call_estimates'] or 0
            
            call_to_estimate_rate = (calls_with_estimates / total_calls * 100) if total_calls > 0 else 0
            estimate_to_job_rate = (jobs_from_call_estimates / estimates_from_calls * 100) if estimates_from_calls > 0 else 0
            
            return {
                'call_to_estimate_rate': call_to_estimate_rate,
                'estimate_to_job_rate': estimate_to_job_rate,
                'total_calls': total_calls,
                'estimates_from_calls': estimates_from_calls,
                'jobs_from_estimates': jobs_from_call_estimates
            }
    except Exception as e:
        print(f"Error calculating conversion metrics: {e}")
    
    return {'call_to_estimate_rate': 0, 'estimate_to_job_rate': 0, 'total_calls': 0, 'estimates_from_calls': 0, 'jobs_from_estimates': 0}

def get_previous_period_success_rate(start_date, end_date):
    """Get success rate for the previous period (for delta comparison)"""
    from datetime import timedelta
    
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date
    
    query = """
        SELECT 
            COUNT(*) as total_calls,
            COUNT(CASE WHEN call_status = 'completed' THEN 1 END) as successful_calls
        FROM ai_calls 
        WHERE created_at >= %s AND created_at < %s
    """
    
    try:
        result = execute_query(query, (prev_start, prev_end), fetch=True)
        if result:
            total = result[0]['total_calls'] or 0
            successful = result[0]['successful_calls'] or 0
            return (successful / total * 100) if total > 0 else 0
    except Exception as e:
        print(f"Error calculating previous period success rate: {e}")
    
    return 0

def get_call_performance_trends(days=30):
    """Get call performance trends over time"""
    from datetime import timedelta, date
    
    query = """
        SELECT 
            DATE(created_at) as call_date,
            COUNT(*) as total_calls,
            COUNT(CASE WHEN call_status = 'completed' THEN 1 END) as successful_calls,
            AVG(call_duration) as avg_duration,
            COUNT(CASE WHEN follow_up_required = TRUE THEN 1 END) as follow_ups_needed
        FROM ai_calls 
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY call_date DESC
    """
    
    start_date = date.today() - timedelta(days=days)
    return execute_query(query, (start_date,), fetch=True) or []

def get_call_outcome_analysis():
    """Analyze call outcomes and patterns"""
    query = """
        SELECT 
            call_type,
            call_status,
            COUNT(*) as count,
            AVG(call_duration) as avg_duration,
            COUNT(CASE WHEN follow_up_required = TRUE THEN 1 END) as follow_up_rate
        FROM ai_calls 
        WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY call_type, call_status
        ORDER BY call_type, call_status
    """
    return execute_query(query, fetch=True) or []
