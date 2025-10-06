import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from database import add_financial_record, get_financial_summary, get_monthly_revenue, execute_query
from datetime import datetime, date, timedelta

REQUIRED_ROLE = 'admin'

def show():
    st.markdown("# 💰 Financial Dashboard")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Add Transaction", "Reports", "Analytics", "Advanced P&L"])
    
    with tab1:
        show_financial_overview()
    
    with tab2:
        show_add_transaction()
    
    with tab3:
        show_financial_reports()
    
    with tab4:
        show_financial_analytics()
    
    with tab5:
        show_advanced_pl_reporting()

def show_financial_overview():
    st.subheader("Financial Overview")
    
    # Get financial summary
    financial_data = get_financial_summary()
    monthly_data = get_monthly_revenue()
    
    # Calculate key metrics
    total_income = 0
    total_expenses = 0
    
    for record in financial_data:
        if record['record_type'] == 'income':
            total_income = record['total_amount']
        elif record['record_type'] == 'expense':
            total_expenses = record['total_amount']
    
    net_profit = total_income - total_expenses
    profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
    
    # Key metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", f"${total_income:,.2f}", delta=None)
    
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}", delta=None)
    
    with col3:
        delta_color = "normal" if net_profit >= 0 else "inverse"
        st.metric("Net Profit", f"${net_profit:,.2f}", delta=f"{profit_margin:.1f}%")
    
    with col4:
        # Calculate this month vs last month
        current_month_revenue = 0
        if monthly_data:
            current_month_revenue = monthly_data[-1]['revenue'] if monthly_data[-1]['revenue'] else 0
        st.metric("This Month Revenue", f"${current_month_revenue:,.2f}")
    
    st.markdown("---")
    
    # Revenue vs Expenses Chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Revenue vs Expenses")
        if monthly_data:
            months = [row['month'].strftime('%Y-%m') for row in monthly_data]
            revenue = [float(row['revenue']) for row in monthly_data]
            expenses = [float(row['expenses']) for row in monthly_data]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=revenue, mode='lines+markers', name='Revenue', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=months, y=expenses, mode='lines+markers', name='Expenses', line=dict(color='red')))
            
            fig.update_layout(
                title="Monthly Revenue vs Expenses",
                xaxis_title="Month",
                yaxis_title="Amount ($)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No monthly financial data available")
    
    with col2:
        st.subheader("🥧 Income vs Expenses Breakdown")
        if financial_data:
            labels = []
            values = []
            colors = []
            
            for record in financial_data:
                if record['record_type'] == 'income':
                    labels.append('Income')
                    values.append(float(record['total_amount']))
                    colors.append('#2E8B57')  # Green
                elif record['record_type'] == 'expense':
                    labels.append('Expenses')
                    values.append(float(record['total_amount']))
                    colors.append('#DC143C')  # Red
            
            if values:
                fig = px.pie(values=values, names=labels, title="Financial Distribution")
                fig.update_traces(marker=dict(colors=colors))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No financial data available")
    
    # Recent transactions
    st.subheader("🕒 Recent Transactions")
    recent_transactions = execute_query("""
        SELECT fr.*, j.job_title 
        FROM financial_records fr 
        LEFT JOIN jobs j ON fr.job_id = j.id 
        ORDER BY fr.created_at DESC 
        LIMIT 10
    """, fetch=True)
    
    if recent_transactions:
        for transaction in recent_transactions:
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**{transaction['description'] or 'N/A'}**")
                if transaction['job_title']:
                    st.write(f"Job: {transaction['job_title']}")
                else:
                    st.write(f"Category: {transaction['category'] or 'General'}")
            
            with col2:
                st.write(f"Date: {transaction['transaction_date'].strftime('%m/%d/%Y')}")
                st.write(f"Type: {transaction['record_type'].title()}")
            
            with col3:
                amount_color = "green" if transaction['record_type'] == 'income' else "red"
                prefix = "+" if transaction['record_type'] == 'income' else "-"
                st.markdown(f"<span style='color:{amount_color}'>{prefix}${transaction['amount']:,.2f}</span>", unsafe_allow_html=True)
            
            with col4:
                st.write(f"Added: {transaction['created_at'].strftime('%m/%d')}")
        
        st.markdown("---")
    else:
        st.info("No recent transactions found")

def show_add_transaction():
    st.subheader("Add New Transaction")
    
    with st.form("add_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            record_type = st.selectbox("Transaction Type", ["income", "expense"])
            amount = st.number_input("Amount ($)", min_value=0.01, format="%.2f")
            description = st.text_input("Description", placeholder="Payment from client, Equipment purchase, etc.")
            transaction_date = st.date_input("Transaction Date", value=date.today())
        
        with col2:
            category = st.selectbox(
                "Category",
                [
                    "Client Payment",
                    "Equipment Purchase", 
                    "Materials",
                    "Labor Costs",
                    "Vehicle Expenses",
                    "Insurance",
                    "Marketing",
                    "Office Expenses",
                    "Subcontractor Payment",
                    "Other"
                ]
            )
            
            # Get jobs for association
            jobs_query = "SELECT id, job_title, client_name FROM jobs ORDER BY created_at DESC"
            jobs = execute_query(jobs_query, fetch=True) or []
            
            job_options = ["None - General Transaction"] + [f"#{job['id']} - {job['job_title']} ({job['client_name']})" for job in jobs]
            selected_job = st.selectbox("Associate with Job (Optional)", job_options)
            
            # Extract job ID if selected
            job_id = None
            if selected_job != "None - General Transaction":
                job_id = int(selected_job.split("#")[1].split(" -")[0])
        
        submitted = st.form_submit_button("Add Transaction", use_container_width=True)
        
        if submitted:
            if amount > 0 and description.strip():
                transaction_data = {
                    'record_type': record_type,
                    'amount': amount,
                    'description': description,
                    'category': category,
                    'job_id': job_id,
                    'transaction_date': transaction_date
                }
                
                transaction_id = add_financial_record(transaction_data)
                if transaction_id:
                    st.success(f"✅ Transaction #{transaction_id} added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add transaction. Please try again.")
            else:
                st.error("❌ Please fill in all required fields with valid values.")

def show_financial_reports():
    st.subheader("📈 Financial Reports")
    
    # Date range selector
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    with col3:
        report_type = st.selectbox("Report Type", ["Summary", "Detailed", "By Category", "By Job"])
    
    if st.button("Generate Report", use_container_width=True):
        # Get transactions for date range
        query = """
            SELECT fr.*, j.job_title, j.client_name 
            FROM financial_records fr 
            LEFT JOIN jobs j ON fr.job_id = j.id 
            WHERE fr.transaction_date BETWEEN %s AND %s 
            ORDER BY fr.transaction_date DESC
        """
        transactions = execute_query(query, (start_date, end_date), fetch=True)
        
        if transactions:
            if report_type == "Summary":
                show_summary_report(transactions, start_date, end_date)
            elif report_type == "Detailed":
                show_detailed_report(transactions)
            elif report_type == "By Category":
                show_category_report(transactions)
            elif report_type == "By Job":
                show_job_report(transactions)
        else:
            st.info("No transactions found for the selected date range.")

def show_summary_report(transactions, start_date, end_date):
    st.subheader(f"Summary Report: {start_date} to {end_date}")
    
    # Calculate totals
    total_income = sum([t['amount'] for t in transactions if t['record_type'] == 'income'])
    total_expenses = sum([t['amount'] for t in transactions if t['record_type'] == 'expense'])
    net_profit = total_income - total_expenses
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st.metric("Net Profit", f"${net_profit:,.2f}")
    
    # Transaction count by type
    income_count = len([t for t in transactions if t['record_type'] == 'income'])
    expense_count = len([t for t in transactions if t['record_type'] == 'expense'])
    
    st.write(f"**Transaction Count:** {len(transactions)} total ({income_count} income, {expense_count} expenses)")

def show_detailed_report(transactions):
    st.subheader("Detailed Transaction Report")
    
    # Create DataFrame for better display
    df_data = []
    for t in transactions:
        df_data.append({
            'Date': t['transaction_date'].strftime('%m/%d/%Y'),
            'Type': t['record_type'].title(),
            'Amount': f"${t['amount']:,.2f}",
            'Description': t['description'] or 'N/A',
            'Category': t['category'] or 'N/A',
            'Job': t['job_title'] or 'General',
            'Client': t['client_name'] or 'N/A'
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)

def show_category_report(transactions):
    st.subheader("Report by Category")
    
    # Group by category
    category_data = {}
    for t in transactions:
        category = t['category'] or 'Uncategorized'
        if category not in category_data:
            category_data[category] = {'income': 0, 'expense': 0, 'count': 0}
        
        if t['record_type'] == 'income':
            category_data[category]['income'] += t['amount']
        else:
            category_data[category]['expense'] += t['amount']
        category_data[category]['count'] += 1
    
    # Display category breakdown
    for category, data in category_data.items():
        net = data['income'] - data['expense']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"**{category}**")
        with col2:
            st.write(f"Income: ${data['income']:,.2f}")
        with col3:
            st.write(f"Expenses: ${data['expense']:,.2f}")
        with col4:
            color = "green" if net >= 0 else "red"
            st.markdown(f"<span style='color:{color}'>Net: ${net:,.2f}</span>", unsafe_allow_html=True)

def show_job_report(transactions):
    st.subheader("Report by Job")
    
    # Group by job
    job_data = {}
    for t in transactions:
        job_key = t['job_title'] if t['job_title'] else 'General/Unassigned'
        if job_key not in job_data:
            job_data[job_key] = {'income': 0, 'expense': 0, 'count': 0, 'client': t['client_name']}
        
        if t['record_type'] == 'income':
            job_data[job_key]['income'] += t['amount']
        else:
            job_data[job_key]['expense'] += t['amount']
        job_data[job_key]['count'] += 1
    
    # Display job breakdown
    for job, data in job_data.items():
        net = data['income'] - data['expense']
        
        st.write(f"**{job}**")
        if data['client']:
            st.write(f"Client: {data['client']}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"Income: ${data['income']:,.2f}")
        with col2:
            st.write(f"Expenses: ${data['expense']:,.2f}")
        with col3:
            color = "green" if net >= 0 else "red"
            st.markdown(f"<span style='color:{color}'>Net: ${net:,.2f}</span>", unsafe_allow_html=True)
        with col4:
            st.write(f"Transactions: {data['count']}")
        
        st.markdown("---")

def show_financial_analytics():
    st.subheader("📊 Enhanced Financial Analytics & Forecasting")
    
    # Profit margin analysis
    monthly_data = get_monthly_revenue()
    
    if monthly_data:
        # Prepare data for analysis
        df_monthly = pd.DataFrame([
            {
                'Month': row['month'].strftime('%Y-%m'),
                'Date': row['month'],
                'Revenue': float(row['revenue']),
                'Expenses': float(row['expenses']),
                'Profit': float(row['revenue']) - float(row['expenses']),
                'Profit Margin': ((float(row['revenue']) - float(row['expenses'])) / float(row['revenue']) * 100) if float(row['revenue']) > 0 else 0
            }
            for row in monthly_data
        ])
        
        # Enhanced Analytics Dashboard
        st.subheader("🎯 Performance Metrics & Forecasting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue Trend with Forecasting
            fig = create_revenue_forecast(df_monthly)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Profit Margin Trend with Moving Average
            fig = create_profit_margin_analysis(df_monthly)
            st.plotly_chart(fig, use_container_width=True)
        
        # Advanced Financial Metrics
        st.subheader("📈 Advanced Performance Indicators")
        
        # Calculate advanced metrics
        advanced_metrics = calculate_advanced_metrics(df_monthly)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Revenue Growth Rate", f"{advanced_metrics['revenue_growth']:.1f}%", 
                     delta=f"{advanced_metrics['growth_acceleration']:.1f}%")
        with col2:
            st.metric("Average Monthly Revenue", f"${advanced_metrics['avg_revenue']:,.0f}")
        with col3:
            st.metric("Revenue Volatility", f"{advanced_metrics['revenue_volatility']:.1f}%")
        with col4:
            st.metric("Break-even Point", f"${advanced_metrics['breakeven']:,.0f}")
        
        # Financial Health Score
        st.subheader("💪 Financial Health Dashboard")
        
        health_score = calculate_financial_health_score(df_monthly)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Financial Health Gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = health_score['score'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Financial Health Score"},
                delta = {'reference': 75},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "gray"},
                        {'range': [75, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.write("**Health Score Components:**")
            for component, score in health_score['components'].items():
                color = "green" if score > 70 else "orange" if score > 40 else "red"
                st.markdown(f"• **{component}**: <span style='color:{color}'>{score:.0f}/100</span>", unsafe_allow_html=True)
            
            st.write(f"**Overall Assessment**: {health_score['assessment']}")
        
        # Cash Flow Forecast
        st.subheader("💰 Cash Flow Forecast")
        
        forecast_months = 6
        cash_flow_forecast = generate_cash_flow_forecast(df_monthly, forecast_months)
        
        fig = px.line(cash_flow_forecast, x='Month', y=['Projected Revenue', 'Projected Expenses', 'Projected Profit'],
                     title=f'{forecast_months}-Month Cash Flow Forecast')
        fig.update_layout(yaxis_title="Amount ($)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Budget vs Actual Analysis
        st.subheader("🎯 Budget vs Actual Performance")
        show_budget_analysis(df_monthly)
        
        # Key insights and recommendations
        st.subheader("🔍 AI-Powered Financial Insights")
        show_financial_insights(df_monthly, advanced_metrics, health_score)
        
        # Show the enhanced data table
        st.subheader("📄 Detailed Monthly Financial Analysis")
        enhanced_df = df_monthly.copy()
        enhanced_df['ROI %'] = ((enhanced_df['Profit'] / enhanced_df['Expenses'].replace(0, np.nan)) * 100).round(1)
        enhanced_df['Revenue Growth %'] = enhanced_df['Revenue'].pct_change().multiply(100).round(1)
        st.dataframe(enhanced_df, use_container_width=True)
    else:
        st.info("No monthly financial data available for analysis. Start adding transactions to see advanced analytics and forecasting.")

def show_advanced_pl_reporting():
    """Comprehensive Profit & Loss Statement with Industry-Standard Formatting"""
    st.subheader("📋 Advanced Profit & Loss Statement")
    
    # Date range selector
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    with col3:
        comparison_period = st.selectbox("Compare To", ["None", "Previous Period", "Same Period Last Year"])
    
    if st.button("Generate P&L Statement", use_container_width=True):
        # Generate comprehensive P&L statement
        pl_data = generate_pl_statement(start_date, end_date, comparison_period)
        
        if pl_data:
            display_pl_statement(pl_data, start_date, end_date, comparison_period)
        else:
            st.info("No financial data available for the selected period.")

def generate_pl_statement(start_date, end_date, comparison_period):
    """Generate detailed P&L statement data"""
    # Get transactions for the period
    query = """
        SELECT fr.*, j.job_title, j.client_name
        FROM financial_records fr 
        LEFT JOIN jobs j ON fr.job_id = j.id 
        WHERE fr.transaction_date BETWEEN %s AND %s 
        ORDER BY fr.transaction_date DESC
    """
    transactions = execute_query(query, (start_date, end_date), fetch=True)
    
    if not transactions:
        return None
    
    # Categorize income and expenses
    revenue_categories = {
        'Client Payment': 0,
        'Other Income': 0
    }
    
    expense_categories = {
        'Materials': 0,
        'Labor Costs': 0,
        'Equipment Purchase': 0,
        'Vehicle Expenses': 0,
        'Insurance': 0,
        'Marketing': 0,
        'Office Expenses': 0,
        'Subcontractor Payment': 0,
        'Other Expenses': 0
    }
    
    # Process transactions
    for t in transactions:
        if t['record_type'] == 'income':
            if t['category'] == 'Client Payment':
                revenue_categories['Client Payment'] += t['amount']
            else:
                revenue_categories['Other Income'] += t['amount']
        else:
            category = t['category'] or 'Other Expenses'
            if category in expense_categories:
                expense_categories[category] += t['amount']
            else:
                expense_categories['Other Expenses'] += t['amount']
    
    # Calculate comparison data if requested
    comparison_data = None
    if comparison_period != "None":
        comparison_data = get_comparison_period_data(start_date, end_date, comparison_period)
    
    return {
        'revenue': revenue_categories,
        'expenses': expense_categories,
        'comparison': comparison_data,
        'period': f"{start_date} to {end_date}",
        'total_revenue': sum(revenue_categories.values()),
        'total_expenses': sum(expense_categories.values())
    }

def get_comparison_period_data(start_date, end_date, comparison_type):
    """Get data for comparison period"""
    if comparison_type == "Previous Period":
        period_length = (end_date - start_date).days
        comp_end = start_date - timedelta(days=1)
        comp_start = comp_end - timedelta(days=period_length)
    elif comparison_type == "Same Period Last Year":
        comp_start = start_date.replace(year=start_date.year - 1)
        comp_end = end_date.replace(year=end_date.year - 1)
    else:
        return None
    
    return generate_pl_statement(comp_start, comp_end, "None")

def display_pl_statement(pl_data, start_date, end_date, comparison_period):
    """Display formatted P&L statement"""
    st.subheader(f"P&L Statement: {pl_data['period']}")
    
    # Create formatted P&L table
    if comparison_period != "None":
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write("**Account**")
        with col2:
            st.write("**Current Period**")
        with col3:
            st.write(f"**{comparison_period}**")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Account**")
        with col2:
            st.write("**Current Period**")
    
    st.markdown("---")
    
    # Revenue Section
    st.write("**REVENUE**")
    total_revenue = 0
    for category, amount in pl_data['revenue'].items():
        if amount > 0:
            if comparison_period != "None":
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"  {category}")
                with col2:
                    st.write(f"${amount:,.2f}")
                with col3:
                    if pl_data['comparison']:
                        comp_amount = pl_data['comparison']['revenue'].get(category, 0)
                        change = ((amount - comp_amount) / comp_amount * 100) if comp_amount > 0 else 0
                        st.write(f"${comp_amount:,.2f} ({change:+.1f}%)")
                    else:
                        st.write("N/A")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"  {category}")
                with col2:
                    st.write(f"${amount:,.2f}")
            total_revenue += amount
    
    # Total Revenue
    if comparison_period != "None":
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write("**Total Revenue**")
        with col2:
            st.write(f"**${total_revenue:,.2f}**")
        with col3:
            if pl_data['comparison']:
                comp_revenue = pl_data['comparison']['total_revenue']
                revenue_change = ((total_revenue - comp_revenue) / comp_revenue * 100) if comp_revenue > 0 else 0
                st.write(f"**${comp_revenue:,.2f} ({revenue_change:+.1f}%)**")
            else:
                st.write("**N/A**")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Total Revenue**")
        with col2:
            st.write(f"**${total_revenue:,.2f}**")
    
    st.markdown("---")
    
    # Expenses Section
    st.write("**EXPENSES**")
    total_expenses = 0
    for category, amount in pl_data['expenses'].items():
        if amount > 0:
            if comparison_period != "None":
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"  {category}")
                with col2:
                    st.write(f"${amount:,.2f}")
                with col3:
                    if pl_data['comparison']:
                        comp_amount = pl_data['comparison']['expenses'].get(category, 0)
                        change = ((amount - comp_amount) / comp_amount * 100) if comp_amount > 0 else 0
                        st.write(f"${comp_amount:,.2f} ({change:+.1f}%)")
                    else:
                        st.write("N/A")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"  {category}")
                with col2:
                    st.write(f"${amount:,.2f}")
            total_expenses += amount
    
    # Total Expenses
    if comparison_period != "None":
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write("**Total Expenses**")
        with col2:
            st.write(f"**${total_expenses:,.2f}**")
        with col3:
            if pl_data['comparison']:
                comp_expenses = pl_data['comparison']['total_expenses']
                expense_change = ((total_expenses - comp_expenses) / comp_expenses * 100) if comp_expenses > 0 else 0
                st.write(f"**${comp_expenses:,.2f} ({expense_change:+.1f}%)**")
            else:
                st.write("**N/A**")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Total Expenses**")
        with col2:
            st.write(f"**${total_expenses:,.2f}**")
    
    st.markdown("---")
    
    # Net Profit
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    if comparison_period != "None":
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write("**NET PROFIT**")
        with col2:
            color = "green" if net_profit >= 0 else "red"
            st.markdown(f"**<span style='color:{color}'>${net_profit:,.2f} ({profit_margin:.1f}%)</span>**", unsafe_allow_html=True)
        with col3:
            if pl_data['comparison']:
                comp_profit = pl_data['comparison']['total_revenue'] - pl_data['comparison']['total_expenses']
                profit_change = ((net_profit - comp_profit) / abs(comp_profit) * 100) if comp_profit != 0 else 0
                comp_margin = (comp_profit / pl_data['comparison']['total_revenue'] * 100) if pl_data['comparison']['total_revenue'] > 0 else 0
                comp_color = "green" if comp_profit >= 0 else "red"
                st.markdown(f"**<span style='color:{comp_color}'>${comp_profit:,.2f} ({comp_margin:.1f}%)</span>**", unsafe_allow_html=True)
                st.write(f"Change: {profit_change:+.1f}%")
            else:
                st.write("**N/A**")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**NET PROFIT**")
        with col2:
            color = "green" if net_profit >= 0 else "red"
            st.markdown(f"**<span style='color:{color}'>${net_profit:,.2f} ({profit_margin:.1f}%)</span>**", unsafe_allow_html=True)

def create_revenue_forecast(df_monthly):
    """Create revenue forecast chart with trend analysis"""
    if len(df_monthly) < 3:
        # Simple forecast for limited data
        avg_revenue = df_monthly['Revenue'].mean()
        trend = df_monthly['Revenue'].iloc[-1] - df_monthly['Revenue'].iloc[0] if len(df_monthly) > 1 else 0
        
        fig = px.line(df_monthly, x='Month', y='Revenue', title='Revenue Trend with Basic Forecast')
        return fig
    
    # Calculate moving average and trend
    df_monthly['MA_3'] = df_monthly['Revenue'].rolling(window=3).mean()
    
    # Simple linear trend for forecasting
    from datetime import datetime
    import numpy as np
    
    # Convert months to numeric for trend analysis
    numeric_months = pd.to_numeric(pd.to_datetime(df_monthly['Date']))
    revenue_values = df_monthly['Revenue'].values
    
    # Fit linear trend
    trend_coeff = np.polyfit(range(len(revenue_values)), revenue_values, 1)
    trend_line = np.polyval(trend_coeff, range(len(revenue_values)))
    
    # Create forecast for next 6 months
    future_months = 6
    future_trend = np.polyval(trend_coeff, range(len(revenue_values), len(revenue_values) + future_months))
    
    # Create chart
    fig = go.Figure()
    
    # Actual revenue
    fig.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['Revenue'], 
                            mode='lines+markers', name='Actual Revenue', line=dict(color='blue')))
    
    # Moving average
    fig.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['MA_3'], 
                            mode='lines', name='3-Month Moving Average', line=dict(color='orange', dash='dot')))
    
    # Forecast (simplified)
    last_month_date = df_monthly['Date'].iloc[-1]
    forecast_months = []
    forecast_values = []
    
    for i in range(1, future_months + 1):
        future_date = last_month_date + pd.DateOffset(months=i)
        forecast_months.append(future_date.strftime('%Y-%m'))
        
        # Simple forecast: trend + seasonality adjustment
        seasonal_factor = 1.0  # Could be enhanced with actual seasonality
        forecast_value = max(0, trend_line[-1] + (trend_coeff[0] * i) * seasonal_factor)
        forecast_values.append(forecast_value)
    
    # Add forecast line
    all_months = list(df_monthly['Month']) + forecast_months
    all_values = list(df_monthly['Revenue']) + forecast_values
    
    fig.add_trace(go.Scatter(x=all_months[-future_months-1:], y=all_values[-future_months-1:], 
                            mode='lines+markers', name='Forecast', 
                            line=dict(color='red', dash='dash'), marker=dict(symbol='diamond')))
    
    fig.update_layout(title='Revenue Trend with 6-Month Forecast', 
                      xaxis_title='Month', yaxis_title='Revenue ($)')
    
    return fig

def create_profit_margin_analysis(df_monthly):
    """Create profit margin analysis with benchmarks"""
    # Industry benchmark for construction businesses (example)
    industry_benchmark = 15.0  # 15% profit margin
    
    fig = go.Figure()
    
    # Actual profit margin
    fig.add_trace(go.Scatter(x=df_monthly['Month'], y=df_monthly['Profit Margin'], 
                            mode='lines+markers', name='Profit Margin', line=dict(color='green')))
    
    # Industry benchmark line
    fig.add_hline(y=industry_benchmark, line_dash="dash", line_color="gray", 
                  annotation_text="Industry Benchmark (15%)")
    
    # Moving average
    if len(df_monthly) >= 3:
        ma_margin = df_monthly['Profit Margin'].rolling(window=3).mean()
        fig.add_trace(go.Scatter(x=df_monthly['Month'], y=ma_margin, 
                                mode='lines', name='3-Month Average', line=dict(color='orange', dash='dot')))
    
    fig.update_layout(title='Profit Margin Analysis with Benchmark', 
                      xaxis_title='Month', yaxis_title='Profit Margin (%)')
    
    return fig

def calculate_advanced_metrics(df_monthly):
    """Calculate advanced financial performance metrics"""
    if len(df_monthly) < 2:
        return {
            'revenue_growth': 0,
            'growth_acceleration': 0,
            'avg_revenue': df_monthly['Revenue'].mean() if len(df_monthly) > 0 else 0,
            'revenue_volatility': 0,
            'breakeven': df_monthly['Expenses'].mean() if len(df_monthly) > 0 else 0
        }
    
    # Revenue growth rate (month-over-month)
    revenue_growth = df_monthly['Revenue'].pct_change().mean() * 100
    
    # Growth acceleration (change in growth rate)
    growth_rates = df_monthly['Revenue'].pct_change() * 100
    growth_acceleration = growth_rates.diff().mean() if len(growth_rates) > 1 else 0
    
    # Revenue volatility (coefficient of variation)
    avg_revenue = df_monthly['Revenue'].mean()
    revenue_std = df_monthly['Revenue'].std()
    revenue_volatility = (revenue_std / avg_revenue * 100) if avg_revenue > 0 else 0
    
    # Break-even point (average expenses)
    breakeven = df_monthly['Expenses'].mean()
    
    return {
        'revenue_growth': revenue_growth,
        'growth_acceleration': growth_acceleration,
        'avg_revenue': avg_revenue,
        'revenue_volatility': revenue_volatility,
        'breakeven': breakeven
    }

def calculate_financial_health_score(df_monthly):
    """Calculate comprehensive financial health score"""
    if len(df_monthly) == 0:
        return {'score': 0, 'components': {}, 'assessment': 'No data available'}
    
    # Component scores (0-100)
    components = {}
    
    # 1. Profitability Score
    avg_margin = df_monthly['Profit Margin'].mean()
    profitability_score = min(100, max(0, (avg_margin + 10) * 5))  # -10% = 0, +10% = 100
    components['Profitability'] = profitability_score
    
    # 2. Growth Score
    if len(df_monthly) > 1:
        recent_growth = df_monthly['Revenue'].iloc[-3:].mean() / df_monthly['Revenue'].iloc[:3].mean() if len(df_monthly) >= 6 else df_monthly['Revenue'].iloc[-1] / df_monthly['Revenue'].iloc[0]
        growth_score = min(100, max(0, (recent_growth - 0.8) * 500))  # 20% decline = 0, 20% growth = 100
    else:
        growth_score = 50
    components['Growth'] = growth_score
    
    # 3. Stability Score
    revenue_cv = (df_monthly['Revenue'].std() / df_monthly['Revenue'].mean()) if df_monthly['Revenue'].mean() > 0 else 1
    stability_score = max(0, 100 - (revenue_cv * 200))  # Lower volatility = higher score
    components['Stability'] = stability_score
    
    # 4. Cash Flow Score
    positive_months = len(df_monthly[df_monthly['Profit'] > 0])
    cash_flow_score = (positive_months / len(df_monthly)) * 100
    components['Cash Flow'] = cash_flow_score
    
    # Overall score (weighted average)
    overall_score = (
        profitability_score * 0.3 +
        growth_score * 0.25 +
        stability_score * 0.20 +
        cash_flow_score * 0.25
    )
    
    # Assessment
    if overall_score >= 80:
        assessment = "Excellent - Strong financial performance across all metrics"
    elif overall_score >= 65:
        assessment = "Good - Solid financial foundation with room for improvement"
    elif overall_score >= 50:
        assessment = "Fair - Some concerns, focus on improving weaker areas"
    else:
        assessment = "Needs Attention - Significant financial challenges require immediate action"
    
    return {
        'score': overall_score,
        'components': components,
        'assessment': assessment
    }

def generate_cash_flow_forecast(df_monthly, forecast_months):
    """Generate cash flow forecast based on historical trends"""
    if len(df_monthly) == 0:
        return pd.DataFrame()
    
    # Calculate trend coefficients
    revenue_trend = np.polyfit(range(len(df_monthly)), df_monthly['Revenue'].values, 1)
    expense_trend = np.polyfit(range(len(df_monthly)), df_monthly['Expenses'].values, 1)
    
    # Generate forecast data
    forecast_data = []
    last_date = df_monthly['Date'].iloc[-1]
    
    for i in range(1, forecast_months + 1):
        future_date = last_date + pd.DateOffset(months=i)
        
        # Project revenue and expenses with trend
        projected_revenue = max(0, np.polyval(revenue_trend, len(df_monthly) + i - 1))
        projected_expenses = max(0, np.polyval(expense_trend, len(df_monthly) + i - 1))
        projected_profit = projected_revenue - projected_expenses
        
        # Add seasonality factor (simplified)
        month_factor = 1.0 + 0.1 * np.sin(2 * np.pi * (future_date.month - 1) / 12)  # +/- 10% seasonal variation
        projected_revenue *= month_factor
        
        forecast_data.append({
            'Month': future_date.strftime('%Y-%m'),
            'Projected Revenue': projected_revenue,
            'Projected Expenses': projected_expenses,
            'Projected Profit': projected_profit
        })
    
    return pd.DataFrame(forecast_data)

def show_budget_analysis(df_monthly):
    """Show budget vs actual analysis with variance reporting"""
    st.write("**Budget vs Actual Performance Analysis**")
    
    # Simplified budget targets (could be enhanced with user input)
    monthly_revenue_target = df_monthly['Revenue'].quantile(0.75)  # 75th percentile as target
    monthly_expense_budget = df_monthly['Expenses'].quantile(0.5)   # Median as budget
    
    # Calculate variances
    variances = []
    for _, row in df_monthly.iterrows():
        revenue_variance = ((row['Revenue'] - monthly_revenue_target) / monthly_revenue_target * 100) if monthly_revenue_target > 0 else 0
        expense_variance = ((row['Expenses'] - monthly_expense_budget) / monthly_expense_budget * 100) if monthly_expense_budget > 0 else 0
        
        variances.append({
            'Month': row['Month'],
            'Revenue Target': monthly_revenue_target,
            'Actual Revenue': row['Revenue'],
            'Revenue Variance %': revenue_variance,
            'Expense Budget': monthly_expense_budget,
            'Actual Expenses': row['Expenses'],
            'Expense Variance %': expense_variance
        })
    
    variance_df = pd.DataFrame(variances)
    
    # Show variance chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(x=variance_df['Month'], y=variance_df['Revenue Variance %'], 
                         name='Revenue Variance %', marker_color='green'))
    fig.add_trace(go.Bar(x=variance_df['Month'], y=variance_df['Expense Variance %'], 
                         name='Expense Variance %', marker_color='red'))
    
    fig.update_layout(title='Budget Variance Analysis (%)', 
                      xaxis_title='Month', yaxis_title='Variance from Budget (%)',
                      barmode='group')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_rev_variance = variance_df['Revenue Variance %'].mean()
        st.metric("Avg Revenue Variance", f"{avg_rev_variance:+.1f}%")
    with col2:
        avg_exp_variance = variance_df['Expense Variance %'].mean()
        st.metric("Avg Expense Variance", f"{avg_exp_variance:+.1f}%")
    with col3:
        on_target_months = len(variance_df[(variance_df['Revenue Variance %'] > -10) & (variance_df['Revenue Variance %'] < 10)])
        st.metric("Months On-Target", f"{on_target_months}/{len(variance_df)}")

def show_financial_insights(df_monthly, advanced_metrics, health_score):
    """Generate AI-powered financial insights and recommendations"""
    insights = []
    
    # Revenue insights
    if advanced_metrics['revenue_growth'] > 5:
        insights.append("✅ **Strong Revenue Growth**: Your revenue is growing at a healthy pace. Consider scaling operations to maintain this momentum.")
    elif advanced_metrics['revenue_growth'] < -5:
        insights.append("⚠️ **Revenue Declining**: Revenue is showing a downward trend. Focus on customer retention and new client acquisition.")
    else:
        insights.append("📊 **Stable Revenue**: Revenue is stable. Look for opportunities to drive growth through new services or market expansion.")
    
    # Profitability insights
    avg_margin = df_monthly['Profit Margin'].mean()
    if avg_margin > 20:
        insights.append("🎯 **Excellent Margins**: Your profit margins are above industry benchmarks. This indicates strong pricing power and cost control.")
    elif avg_margin > 10:
        insights.append("👍 **Healthy Margins**: Profit margins are solid. Monitor for opportunities to optimize further.")
    elif avg_margin > 0:
        insights.append("📈 **Improving Margins**: Margins are positive but could be optimized. Review pricing strategy and cost management.")
    else:
        insights.append("🚨 **Negative Margins**: Immediate attention needed. Review pricing, reduce costs, or improve operational efficiency.")
    
    # Volatility insights
    if advanced_metrics['revenue_volatility'] > 30:
        insights.append("📉 **High Revenue Volatility**: Consider diversifying revenue streams or implementing recurring revenue models to stabilize cash flow.")
    elif advanced_metrics['revenue_volatility'] < 15:
        insights.append("🎯 **Stable Revenue Pattern**: Low volatility indicates predictable business performance. Good foundation for planning and growth.")
    
    # Seasonal patterns
    if len(df_monthly) >= 12:
        seasonal_insight = analyze_seasonality(df_monthly)
        if seasonal_insight:
            insights.append(seasonal_insight)
    
    # Health score insights
    if health_score['score'] > 80:
        insights.append("💪 **Strong Financial Health**: Overall financial performance is excellent. Focus on sustained growth and market expansion.")
    elif health_score['score'] < 50:
        insights.append("⚠️ **Financial Health Concerns**: Address the key areas identified in the health score components to strengthen your financial position.")
    
    # Display insights
    for insight in insights:
        st.write(insight)
        st.write("")

def analyze_seasonality(df_monthly):
    """Analyze seasonal patterns in revenue"""
    df_monthly['Month_Num'] = pd.to_datetime(df_monthly['Date']).dt.month
    monthly_avg = df_monthly.groupby('Month_Num')['Revenue'].mean()
    
    peak_month = monthly_avg.idxmax()
    low_month = monthly_avg.idxmin()
    
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                   7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    
    peak_value = monthly_avg[peak_month]
    low_value = monthly_avg[low_month]
    
    if (peak_value - low_value) / low_value > 0.3:  # 30% difference indicates seasonality
        return f"📅 **Seasonal Pattern Detected**: {month_names[peak_month]} is typically your strongest month, while {month_names[low_month]} is slower. Plan inventory and cash flow accordingly."
    
    return None
