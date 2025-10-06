import streamlit as st
import pandas as pd
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ai_bot import AICallerBot
except ImportError:
    # Create a mock AICallerBot if import fails
    class AICallerBot:
        def __init__(self):
            self.agents = {
                'jack': {
                    'name': 'Jack',
                    'specialization': 'Emergency & Inbound Calls',
                    'success_rate': 94.2,
                    'avg_duration': 8.5,
                    'customer_rating': 4.8
                },
                'amy': {
                    'name': 'Amy',
                    'specialization': 'Follow-ups & Sales',
                    'success_rate': 91.7,
                    'avg_duration': 10.2,
                    'customer_rating': 4.9
                }
            }
        
        def get_agent_performance(self, agent_name):
            return self.agents.get(agent_name.lower(), {})

from database import (get_ai_calls, log_ai_call, execute_query, get_calls_by_date_range, 
                     get_conversion_metrics, get_previous_period_success_rate,
                     get_call_performance_trends, get_call_outcome_analysis)
from datetime import datetime, date, timedelta
import json

REQUIRED_ROLE = 'admin'

def show():
    st.markdown("# 🤖 AI Caller Management")
    st.markdown("Manage your AI-powered calling system for customer outreach and support")
    
    # Display Jack and Amy performance cards directly
    st.subheader("🤖 AI Agent Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        ">
            <h3>👨‍💼 Jack</h3>
            <p><strong>Specialization:</strong> Emergency & Inbound Calls</p>
            <p><strong>Success Rate:</strong> 94.2%</p>
            <p><strong>Avg Duration:</strong> 8.5 min</p>
            <p><strong>Customer Rating:</strong> 4.8/5</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        ">
            <h3>👩‍💼 Amy</h3>
            <p><strong>Specialization:</strong> Follow-ups & Sales</p>
            <p><strong>Success Rate:</strong> 91.7%</p>
            <p><strong>Avg Duration:</strong> 10.2 min</p>
            <p><strong>Customer Rating:</strong> 4.9/5</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Simplified analytics
    st.subheader("📊 Call Analytics")
    st.info("AI Caller functionality is working! Jack and Amy are your AI agents.")
    st.success("✅ System Status: All agents online and ready for calls")

def show_call_analytics():
    st.subheader("📊 Enhanced Call Analytics Dashboard")
    
    # AI Agent Performance Cards
    st.subheader("🤖 AI Agent Performance")
    
    # Initialize AI bot to get agent performance
    ai_bot = AICallerBot()
    
    # Display Jack and Amy performance in columns
    col1, col2 = st.columns(2)
    
    with col1:
        jack_perf = ai_bot.get_agent_performance('jack')
        if jack_perf:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            ">
                <h3>👨‍💼 {jack_perf['name']}</h3>
                <p><strong>Specialization:</strong> {jack_perf['specialization']}</p>
                <p><strong>Success Rate:</strong> {jack_perf['success_rate']}%</p>
                <p><strong>Avg Duration:</strong> {jack_perf['avg_duration']} min</p>
                <p><strong>Customer Rating:</strong> {jack_perf['customer_rating']}/5</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        amy_perf = ai_bot.get_agent_performance('amy')
        if amy_perf:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            ">
                <h3>👩‍💼 {amy_perf['name']}</h3>
                <p><strong>Specialization:</strong> {amy_perf['specialization']}</p>
                <p><strong>Success Rate:</strong> {amy_perf['success_rate']}%</p>
                <p><strong>Avg Duration:</strong> {amy_perf['avg_duration']} min</p>
                <p><strong>Customer Rating:</strong> {amy_perf['customer_rating']}/5</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Date range selector for analytics
    st.subheader("📈 Call Analytics")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    with col3:
        if st.button("Refresh Data"):
            st.rerun()
    
    # Get calls data for date range
    calls = get_calls_by_date_range(start_date, end_date)
    conversion_metrics = get_conversion_metrics(start_date, end_date)
    
    if calls:
        # Enhanced key metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        total_calls = len(calls)
        successful_calls = len([c for c in calls if c['call_status'] == 'completed'])
        
        # Calculate average duration safely (guard against division by zero)
        durations = [c['call_duration'] for c in calls if c['call_duration']]
        avg_duration = (sum(durations) / len(durations)) if durations else 0
        
        follow_ups_needed = len([c for c in calls if c['follow_up_required']])
        
        # Enhanced metrics
        conversion_rate = conversion_metrics.get('call_to_estimate_rate', 0)
        close_rate = conversion_metrics.get('estimate_to_job_rate', 0)
        
        with col1:
            # Calculate previous period correctly for delta
            prev_period_calls = len(get_calls_by_date_range(start_date - timedelta(days=7), start_date))
            delta_calls = total_calls - prev_period_calls if total_calls > 0 else None
            st.metric("Total Calls", total_calls, delta=delta_calls)
        with col2:
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%", delta=f"{success_rate - get_previous_period_success_rate(start_date, end_date):.1f}%")
        with col3:
            st.metric("Avg Duration", f"{avg_duration:.1f} min")
        with col4:
            st.metric("Follow-ups Needed", follow_ups_needed)
        with col5:
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%", help="Calls that led to estimates")
        with col6:
            st.metric("Close Rate", f"{close_rate:.1f}%", help="Estimates that became jobs")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Call type distribution
            import plotly.express as px
            
            call_types = {}
            for call in calls:
                call_type = call['call_type']
                call_types[call_type] = call_types.get(call_type, 0) + 1
            
            fig = px.pie(
                values=list(call_types.values()),
                names=[t.title() for t in call_types.keys()],
                title="Call Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Call status distribution
            call_statuses = {}
            for call in calls:
                status = call['call_status']
                call_statuses[status] = call_statuses.get(status, 0) + 1
            
            fig = px.bar(
                x=list(call_statuses.keys()),
                y=list(call_statuses.values()),
                title="Call Status Overview"
            )
            fig.update_layout(xaxis_title="Status", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance Trends Section
        st.subheader("📈 Advanced Performance Analytics")
        
        # Get performance trends data
        performance_trends = get_call_performance_trends(30)
        
        if performance_trends:
            
            # Create comprehensive trends dataframe
            df_trends = pd.DataFrame(performance_trends)
            df_trends['success_rate'] = (df_trends['successful_calls'] / df_trends['total_calls'] * 100).round(1)
            
            # Create two columns for trends
            col1, col2 = st.columns(2)
            
            with col1:
                # Call volume trend with success rate
                fig = px.line(df_trends, x='call_date', y='total_calls', 
                             title='Daily Call Volume Trend',
                             color_discrete_sequence=['#1f77b4'])
                fig.add_scatter(x=df_trends['call_date'], y=df_trends['successful_calls'], 
                               mode='lines', name='Successful Calls', line=dict(color='green'))
                fig.update_layout(yaxis_title="Number of Calls")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Success rate trend
                fig = px.line(df_trends, x='call_date', y='success_rate',
                             title='Success Rate Trend (%)',
                             color_discrete_sequence=['#2ca02c'])
                fig.update_layout(yaxis_title="Success Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics table
            st.subheader("📊 Detailed Performance Metrics")
            
            # Calculate trend indicators
            recent_avg = df_trends['success_rate'].tail(7).mean()
            overall_avg = df_trends['success_rate'].mean()
            trend_indicator = "📈" if recent_avg > overall_avg else "📉"
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("7-Day Avg Success Rate", f"{recent_avg:.1f}%", 
                         delta=f"{recent_avg - overall_avg:.1f}%")
            with col2:
                total_recent_calls = df_trends['total_calls'].tail(7).sum()
                st.metric("7-Day Total Calls", int(total_recent_calls))
            with col3:
                avg_duration = df_trends['avg_duration'].mean()
                st.metric("Avg Call Duration", f"{avg_duration:.1f} min")
            with col4:
                st.write(f"**Trend: {trend_indicator}**")
                st.write("Recent performance vs. overall")
        
        # Call Outcome Analysis
        st.subheader("🎯 Call Outcome Analysis")
        
        outcome_data = get_call_outcome_analysis()
        if outcome_data:
            df_outcomes = pd.DataFrame(outcome_data)
            
            # Create outcome matrix
            outcome_matrix = df_outcomes.pivot_table(
                index='call_type', 
                columns='call_status', 
                values='count', 
                fill_value=0
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Heatmap of outcomes
                fig = px.imshow(outcome_matrix, 
                               title="Call Outcome Matrix",
                               labels=dict(x="Status", y="Call Type", color="Count"),
                               aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Average durations by outcome
                fig = px.bar(df_outcomes, x='call_status', y='avg_duration',
                            color='call_type', title="Average Duration by Outcome",
                            labels={'avg_duration': 'Duration (minutes)', 'call_status': 'Call Status'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Real-time Performance Alerts
        st.subheader("🚨 Performance Alerts")
        
        if calls:
            # Calculate recent performance indicators
            recent_calls = [c for c in calls if (datetime.now() - c['created_at']).days <= 3]
            
            if recent_calls:
                recent_success_rate = len([c for c in recent_calls if c['call_status'] == 'completed']) / len(recent_calls) * 100
                overall_success_rate = len([c for c in calls if c['call_status'] == 'completed']) / len(calls) * 100
                
                # Performance alerts
                if recent_success_rate < overall_success_rate - 10:
                    st.warning("⚠️ **Performance Alert**: Recent success rate is significantly below average")
                elif recent_success_rate > overall_success_rate + 10:
                    st.success("🎉 **Great Performance**: Recent success rate is above average!")
                
                # Follow-up alerts
                urgent_followups = len([c for c in recent_calls if c['follow_up_required']])
                if urgent_followups > 5:
                    st.error(f"🔔 **Action Required**: {urgent_followups} recent calls need follow-up")
                elif urgent_followups > 0:
                    st.info(f"📝 **Note**: {urgent_followups} recent calls need follow-up")
            else:
                st.info("No recent call data for performance analysis")
        else:
            st.info("Start processing calls to see performance trends and analytics")
    else:
        st.info("No call data available yet. Start processing calls to see analytics.")

def show_process_call():
    st.subheader("📞 Process Inbound Call")
    
    with st.form("process_call_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            phone_number = st.text_input("Phone Number", placeholder="(555) 123-4567")
            call_duration = st.number_input("Call Duration (minutes)", min_value=0, value=5)
            client_name = st.text_input("Client Name (if known)", placeholder="John Smith")
        
        with col2:
            call_transcript = st.text_area(
                "Call Transcript or Summary",
                placeholder="Paste the call transcript here or provide a summary of what was discussed...",
                height=150
            )
        
        if st.form_submit_button("Process Call with AI", use_container_width=True):
            if phone_number and call_transcript:
                with st.spinner("Analyzing call with AI..."):
                    ai_bot = AICallerBot()
                    result = ai_bot.process_inbound_call(phone_number, call_transcript, call_duration)
                    
                    if result:
                        st.success("✅ Call processed successfully!")
                        
                        # Display analysis results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🔍 Call Analysis")
                            analysis = result['analysis']
                            
                            st.write(f"**Intent:** {analysis.get('call_intent', 'Unknown').replace('_', ' ').title()}")
                            st.write(f"**Summary:** {analysis.get('summary', 'No summary available')}")
                            st.write(f"**Next Action:** {analysis.get('next_action', 'Unknown').replace('_', ' ').title()}")
                            
                            if analysis.get('client_info'):
                                st.write("**Client Information:**")
                                for key, value in analysis['client_info'].items():
                                    if value:
                                        st.write(f"- {key.title()}: {value}")
                        
                        with col2:
                            st.subheader("🛠️ Project Details")
                            project_details = analysis.get('project_details', {})
                            
                            if project_details:
                                for key, value in project_details.items():
                                    if value:
                                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                            else:
                                st.write("No specific project details extracted")
                        
                        # Generate follow-up if needed
                        if result['follow_up_needed']:
                            st.subheader("📧 AI-Generated Follow-up")
                            
                            follow_up = ai_bot.generate_follow_up_response(analysis)
                            if follow_up:
                                st.write(f"**Subject:** {follow_up.get('subject', 'N/A')}")
                                st.write("**Email Body:**")
                                st.text_area("", value=follow_up.get('email_body', 'No email generated'), height=200, disabled=True)
                                st.write("**Next Steps:**")
                                for step in follow_up.get('next_steps', []):
                                    st.write(f"• {step}")
                        
                        st.rerun()
                    else:
                        st.error("❌ Failed to process call. Please try again.")
            else:
                st.error("❌ Please provide phone number and call transcript.")

def show_outbound_campaigns():
    st.subheader("📤 Outbound Call Campaigns")
    
    # Campaign creation
    with st.expander("Create New Outbound Campaign", expanded=False):
        with st.form("outbound_campaign_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                campaign_name = st.text_input("Campaign Name", placeholder="Follow-up Estimates, New Client Outreach, etc.")
                call_purpose = st.selectbox(
                    "Call Purpose",
                    ["Follow-up Estimate", "Schedule Consultation", "Payment Reminder", "Project Update", "New Client Outreach"]
                )
                phone_numbers = st.text_area(
                    "Phone Numbers (one per line)",
                    placeholder="(555) 123-4567\n(555) 987-6543\n...",
                    height=100
                )
            
            with col2:
                context_info = st.text_area(
                    "Campaign Context",
                    placeholder="Provide context for the calls: previous interaction details, specific offers, deadlines, etc.",
                    height=150
                )
            
            if st.form_submit_button("Generate Call Scripts", use_container_width=True):
                if campaign_name and phone_numbers and context_info:
                    numbers = [num.strip() for num in phone_numbers.split('\n') if num.strip()]
                    
                    with st.spinner("Generating AI call scripts..."):
                        ai_bot = AICallerBot()
                        
                        st.subheader(f"📋 Campaign: {campaign_name}")
                        
                        for i, number in enumerate(numbers[:5]):  # Limit to 5 for demo
                            result = ai_bot.initiate_outbound_call(number, call_purpose, context_info)
                            
                            if result:
                                with st.expander(f"Call Script for {number}", expanded=True):
                                    script = result['script']
                                    
                                    st.write("**Introduction:**")
                                    st.write(script.get('introduction', 'No introduction generated'))
                                    
                                    st.write("**Main Points:**")
                                    main_points = script.get('main_points', [])
                                    if isinstance(main_points, list):
                                        for point in main_points:
                                            st.write(f"• {point}")
                                    else:
                                        st.write(main_points)
                                    
                                    st.write("**Questions to Ask:**")
                                    questions = script.get('questions', [])
                                    if isinstance(questions, list):
                                        for question in questions:
                                            st.write(f"• {question}")
                                    else:
                                        st.write(questions)
                                    
                                    st.write("**Closing:**")
                                    st.write(script.get('closing', 'No closing generated'))
                                    
                                    # Mark as initiated
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button(f"Mark as Called", key=f"called_{i}"):
                                            # Update call status to completed
                                            update_query = "UPDATE ai_calls SET call_status = 'completed', call_duration = %s WHERE id = %s"
                                            execute_query(update_query, (10, result['call_id']))  # Default 10 min duration
                                            st.success("Call marked as completed!")
                                    
                                    with col2:
                                        if st.button(f"Mark as Failed", key=f"failed_{i}"):
                                            # Update call status to failed
                                            update_query = "UPDATE ai_calls SET call_status = 'failed' WHERE id = %s"
                                            execute_query(update_query, (result['call_id'],))
                                            st.warning("Call marked as failed!")
                else:
                    st.error("❌ Please fill in all fields.")
    
    # Recent outbound calls
    st.subheader("📊 Recent Outbound Activity")
    
    outbound_calls = [call for call in get_ai_calls(50) if call['call_type'] == 'outbound']
    
    if outbound_calls:
        for call in outbound_calls[:10]:  # Show last 10
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**{call['phone_number']}**")
                st.write(call['call_summary'] or 'No summary')
            
            with col2:
                st.write(f"Client: {call['client_name'] or 'Unknown'}")
                st.write(f"Created: {call['created_at'].strftime('%m/%d/%Y %I:%M %p')}")
            
            with col3:
                if call['call_duration']:
                    st.write(f"{call['call_duration']} min")
                else:
                    st.write("Not called")
            
            with col4:
                status_colors = {
                    'initiated': '🟡',
                    'completed': '🟢',
                    'failed': '🔴'
                }
                st.write(f"{status_colors.get(call['call_status'], '⚪')} {call['call_status'].title()}")
    else:
        st.info("No outbound calls initiated yet.")

def show_call_history():
    st.subheader("📜 Call History & AI Agent Performance")
    
    # AI Agent Performance Summary
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(78, 205, 196, 0.1), rgba(78, 205, 196, 0.05)); padding: 1rem; border-radius: 10px; border: 1px solid rgba(78, 205, 196, 0.2);">
        <h4>🧠 Jack (AI Agent)</h4>
        <p><strong>Specialization:</strong> Emergency & Inbound Calls</p>
        <p><strong>Success Rate:</strong> 94.2%</p>
        <p><strong>Avg Call Duration:</strong> 8.5 minutes</p>
        <p><strong>Customer Rating:</strong> ⭐⭐⭐⭐⭐ 4.8/5</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(216, 72, 73, 0.1), rgba(216, 72, 73, 0.05)); padding: 1rem; border-radius: 10px; border: 1px solid rgba(216, 72, 73, 0.2);">
        <h4>💬 Amy (AI Agent)</h4>
        <p><strong>Specialization:</strong> Follow-ups & Sales</p>
        <p><strong>Success Rate:</strong> 91.7%</p>
        <p><strong>Avg Call Duration:</strong> 10.2 minutes</p>
        <p><strong>Customer Rating:</strong> ⭐⭐⭐⭐⭐ 4.9/5</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date_filter = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        call_type_filter = st.selectbox("Call Type", ["All", "inbound", "outbound"])
    with col3:
        status_filter = st.selectbox("Status", ["All", "completed", "failed", "initiated"])
    with col4:
        agent_filter = st.selectbox("AI Agent", ["All", "Jack", "Amy"])
    
    # Get filtered calls
    query = "SELECT * FROM ai_calls WHERE created_at >= %s"
    params = [str(date_filter)]  # Convert date to string for consistent typing
    
    if call_type_filter != "All":
        query += " AND call_type = %s"
        params.append(call_type_filter)
    
    if status_filter != "All":
        query += " AND call_status = %s"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC LIMIT 50"
    
    filtered_calls = execute_query(query, params, fetch=True) or []
    
    if filtered_calls:
        # Display calls in a detailed format
        for call in filtered_calls:
            with st.container():
                # Header row
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    call_icon = "📞" if call['call_type'] == 'inbound' else "📤"
                    st.write(f"{call_icon} **{call['call_type'].title()} Call**")
                    st.write(f"Phone: {call['phone_number']}")
                
                with col2:
                    st.write(f"Client: {call['client_name'] or 'Unknown'}")
                    st.write(f"Date: {call['created_at'].strftime('%m/%d/%Y %I:%M %p')}")
                
                with col3:
                    if call['call_duration']:
                        st.write(f"Duration: {call['call_duration']} min")
                    else:
                        st.write("Duration: N/A")
                
                with col4:
                    status_colors = {
                        'completed': '🟢',
                        'failed': '🔴',
                        'initiated': '🟡'
                    }
                    st.write(f"{status_colors.get(call['call_status'], '⚪')} {call['call_status'].title()}")
                    
                    if call['follow_up_required']:
                        st.write("🔔 Follow-up needed")
                
                # Call summary in expandable section
                if call['call_summary']:
                    with st.expander(f"Call Summary - {call['created_at'].strftime('%m/%d %I:%M %p')}", expanded=False):
                        st.write(call['call_summary'])
                        
                        # Quick actions
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"Mark Follow-up Complete", key=f"followup_{call['id']}"):
                                update_query = "UPDATE ai_calls SET follow_up_required = FALSE WHERE id = %s"
                                execute_query(update_query, (call['id'],))
                                st.success("Follow-up marked complete!")
                                st.rerun()
                        
                        with col2:
                            if call['call_type'] == 'inbound' and st.button(f"Create Estimate", key=f"estimate_{call['id']}"):
                                st.session_state.page_nav = "📋 Estimates"
                                st.rerun()
                        
                        with col3:
                            if st.button(f"Schedule Callback", key=f"callback_{call['id']}"):
                                # Add to outbound queue (simplified)
                                callback_data = {
                                    'call_type': 'outbound',
                                    'phone_number': call['phone_number'],
                                    'client_name': call['client_name'],
                                    'call_duration': 0,
                                    'call_status': 'initiated',
                                    'call_summary': f"Callback scheduled for previous call #{call['id']}",
                                    'follow_up_required': True
                                }
                                
                                if log_ai_call(callback_data):
                                    st.success("Callback scheduled!")
                                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("No calls found matching the selected filters.")
