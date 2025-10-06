import json
import os
import random
import time
from database import log_ai_call
import streamlit as st

# Simulated AI responses - no API key required
MOCK_AI_ENABLED = True

class AICallerBot:
    def __init__(self):
        self.client = None  # No OpenAI client needed
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
        """Get performance metrics for specific agent"""
        return self.agents.get(agent_name.lower(), {})
    
    def analyze_call_intent(self, call_transcript):
        """Analyze call transcript to determine intent and extract information"""
        try:
            # Simulate AI analysis with realistic responses
            time.sleep(0.5)  # Simulate processing time
            
            # Simple keyword-based analysis for realistic simulation
            transcript_lower = call_transcript.lower()
            
            # Determine intent based on keywords
            if any(word in transcript_lower for word in ['quote', 'estimate', 'price', 'cost', 'how much']):
                intent = 'quote_request'
                next_action = 'send_estimate'
            elif any(word in transcript_lower for word in ['problem', 'issue', 'complaint', 'wrong', 'bad']):
                intent = 'complaint'
                next_action = 'escalate'
            elif any(word in transcript_lower for word in ['follow', 'update', 'status', 'progress']):
                intent = 'follow_up'
                next_action = 'follow_up_call'
            else:
                intent = 'general_inquiry'
                next_action = 'schedule_visit'
            
            # Extract basic project info
            project_type = 'renovation'
            if any(word in transcript_lower for word in ['kitchen', 'bathroom']):
                project_type = 'kitchen/bathroom renovation'
            elif any(word in transcript_lower for word in ['deck', 'patio', 'outdoor']):
                project_type = 'outdoor construction'
            elif any(word in transcript_lower for word in ['roof', 'roofing']):
                project_type = 'roofing'
            elif any(word in transcript_lower for word in ['foundation', 'basement']):
                project_type = 'foundation work'
            
            # Determine urgency
            urgency = 'medium'
            if any(word in transcript_lower for word in ['urgent', 'asap', 'immediately', 'emergency']):
                urgency = 'high'
            elif any(word in transcript_lower for word in ['sometime', 'eventually', 'no rush']):
                urgency = 'low'
            
            return {
                "call_intent": intent,
                "client_info": {
                    "name": "Client", 
                    "phone": "", 
                    "email": ""
                },
                "project_details": {
                    "type": project_type,
                    "description": f"Customer inquiry about {project_type}",
                    "urgency": urgency
                },
                "next_action": next_action,
                "summary": f"Customer called regarding {project_type} with {urgency} priority. Recommended action: {next_action.replace('_', ' ')}"
            }
        except Exception as e:
            st.error(f"Error analyzing call: {str(e)}")
            return None
    
    def generate_follow_up_response(self, call_analysis):
        """Generate appropriate follow-up response based on call analysis"""
        try:
            time.sleep(0.3)  # Simulate processing time
            
            intent = call_analysis.get('call_intent', 'general_inquiry')
            project_type = call_analysis.get('project_details', {}).get('type', 'construction project')
            
            # Generate contextual responses
            if intent == 'quote_request':
                subject = f"Follow-up: Your {project_type} Quote Request"
                email_body = f"""Dear Valued Customer,

Thank you for contacting BuildPro regarding your {project_type}. We appreciate your interest in our services.

Based on our conversation, I understand you're looking for a professional quote for your {project_type}. Our team specializes in high-quality construction work with attention to detail and customer satisfaction.

Next steps:
• We'll schedule a convenient time to visit your property
• Our expert will assess the project scope and requirements
• We'll provide you with a detailed, competitive quote within 2-3 business days

We look forward to the opportunity to work with you on this exciting project!

Best regards,
BuildPro Construction Team"""
                
                next_steps = [
                    "Schedule property visit within 48 hours",
                    "Conduct detailed site assessment", 
                    "Prepare comprehensive quote",
                    "Follow up within 2-3 business days"
                ]
                
            elif intent == 'complaint':
                subject = f"Re: Your Service Concern - We're Here to Help"
                email_body = f"""Dear Valued Customer,

Thank you for bringing your concerns to our attention. At BuildPro, customer satisfaction is our highest priority, and we take all feedback seriously.

We understand your concerns regarding the {project_type} and want to resolve this matter promptly. Our quality assurance team will be reviewing your case immediately.

Please know that we stand behind our work and are committed to making this right. We will contact you within 24 hours to discuss how we can address your concerns and find a satisfactory solution.

Your trust in BuildPro is important to us, and we appreciate the opportunity to make this right.

Sincerely,
BuildPro Customer Service Team"""
                
                next_steps = [
                    "Escalate to quality assurance team",
                    "Schedule follow-up call within 24 hours",
                    "Investigate the reported issue",
                    "Develop resolution plan"
                ]
                
            else:
                subject = f"Thank You for Your Interest in BuildPro Services"
                email_body = f"""Dear Potential Customer,

Thank you for contacting BuildPro about your {project_type}. We're excited about the possibility of working with you!

Our experienced team has been providing quality construction services for years, and we're confident we can help bring your vision to life. Whether it's a small renovation or a major construction project, we approach every job with the same level of professionalism and attention to detail.

We'll be in touch soon to discuss your project in more detail and answer any questions you may have.

Thank you for considering BuildPro for your construction needs!

Best regards,
The BuildPro Team"""
                
                next_steps = [
                    "Follow up call within 2 business days",
                    "Schedule initial consultation",
                    "Provide project information packet",
                    "Prepare preliminary timeline"
                ]
            
            return {
                "subject": subject,
                "email_body": email_body,
                "next_steps": next_steps
            }
        except Exception as e:
            st.error(f"Error generating follow-up: {str(e)}")
            return None
    
    def estimate_project_cost(self, project_description):
        """Generate cost estimate based on project description"""
        try:
            time.sleep(0.8)  # Simulate processing time
            
            desc_lower = project_description.lower()
            
            # Base cost calculation based on project type
            base_cost = 5000  # Default base cost
            complexity = "medium"
            timeline_days = 14
            key_factors = ["Standard construction project"]
            
            # Kitchen projects
            if any(word in desc_lower for word in ['kitchen', 'countertop', 'cabinet']):
                base_cost = 25000
                complexity = "high"
                timeline_days = 21
                key_factors = ["Kitchen appliances", "Plumbing modifications", "Electrical work", "Custom cabinetry"]
            
            # Bathroom projects
            elif any(word in desc_lower for word in ['bathroom', 'shower', 'tub', 'toilet']):
                base_cost = 15000
                complexity = "medium"
                timeline_days = 14
                key_factors = ["Plumbing work", "Tile installation", "Waterproofing", "Ventilation"]
            
            # Roofing projects
            elif any(word in desc_lower for word in ['roof', 'shingle', 'gutter']):
                base_cost = 12000
                complexity = "medium"
                timeline_days = 7
                key_factors = ["Weather dependency", "Material costs", "Safety requirements", "Disposal fees"]
            
            # Deck/outdoor projects
            elif any(word in desc_lower for word in ['deck', 'patio', 'outdoor', 'fence']):
                base_cost = 8000
                complexity = "low"
                timeline_days = 10
                key_factors = ["Weather dependency", "Foundation work", "Material selection", "Permits"]
            
            # Foundation/basement
            elif any(word in desc_lower for word in ['foundation', 'basement', 'crawl space']):
                base_cost = 20000
                complexity = "high"
                timeline_days = 28
                key_factors = ["Excavation", "Waterproofing", "Structural integrity", "Permits required"]
            
            # Flooring projects
            elif any(word in desc_lower for word in ['floor', 'hardwood', 'tile', 'carpet']):
                base_cost = 6000
                complexity = "low"
                timeline_days = 5
                key_factors = ["Subfloor condition", "Material selection", "Room preparation"]
            
            # Size adjustments based on square footage mentions
            if any(word in desc_lower for word in ['large', 'big', 'spacious', '2000', '3000']):
                base_cost *= 1.5
                timeline_days += 7
                key_factors.append("Large project scope")
            elif any(word in desc_lower for word in ['small', 'compact', 'tiny', '500', '800']):
                base_cost *= 0.7
                timeline_days -= 3
                key_factors.append("Compact project scope")
            
            # Complexity adjustments
            if any(word in desc_lower for word in ['custom', 'luxury', 'high-end', 'premium']):
                base_cost *= 1.8
                complexity = "high"
                timeline_days += 14
                key_factors.append("Premium materials and finishes")
            elif any(word in desc_lower for word in ['budget', 'basic', 'simple', 'standard']):
                base_cost *= 0.8
                complexity = "low"
                timeline_days -= 5
                key_factors.append("Cost-effective approach")
            
            # Calculate final estimates
            low_estimate = base_cost * 0.8
            high_estimate = base_cost * 1.3
            materials_cost = base_cost * 0.45
            labor_cost = base_cost * 0.55
            
            # Add random variation for realism
            variation = random.uniform(0.9, 1.1)
            low_estimate *= variation
            high_estimate *= variation
            materials_cost *= variation
            labor_cost *= variation
            
            return {
                "low_estimate": round(low_estimate, 2),
                "high_estimate": round(high_estimate, 2),
                "materials_cost": round(materials_cost, 2),
                "labor_cost": round(labor_cost, 2),
                "timeline_days": max(3, timeline_days),
                "complexity_rating": complexity,
                "key_factors": key_factors
            }
        except Exception as e:
            st.error(f"Error estimating cost: {str(e)}")
            return None
    
    def process_inbound_call(self, phone_number, transcript, duration):
        """Process inbound call and log to database"""
        try:
            # Analyze the call
            analysis = self.analyze_call_intent(transcript)
            if not analysis:
                return None
            
            # Log to database
            call_data = {
                'call_type': 'inbound',
                'phone_number': phone_number,
                'client_name': analysis.get('client_info', {}).get('name', 'Client'),
                'call_duration': duration,
                'call_status': 'completed',
                'call_summary': analysis.get('summary', ''),
                'follow_up_required': analysis.get('next_action') in ['send_estimate', 'schedule_visit', 'follow_up_call']
            }
            
            call_id = log_ai_call(call_data)
            return {
                'call_id': call_id,
                'analysis': analysis,
                'follow_up_needed': call_data['follow_up_required']
            }
        except Exception as e:
            st.error(f"Error processing inbound call: {str(e)}")
            return None
    
    def initiate_outbound_call(self, phone_number, purpose, context):
        """Simulate outbound call initiation"""
        try:
            time.sleep(0.5)  # Simulate processing time
            
            # Generate contextual call scripts based on purpose
            script_templates = {
                "Follow-up Estimate": {
                    "introduction": f"Hello, this is Sarah from BuildPro Construction. I'm calling to follow up on the estimate request we discussed regarding your {context}. I hope you're having a great day!",
                    "main_points": [
                        "We've completed our analysis of your project requirements",
                        "Our team is excited about the opportunity to work with you",
                        "We have some questions to finalize the details",
                        "We can provide a competitive quote within 24-48 hours"
                    ],
                    "questions": [
                        "What's your preferred timeline for starting this project?",
                        "Do you have a budget range in mind for this work?",
                        "Are there any specific materials or finishes you prefer?",
                        "Would you prefer to schedule an in-person consultation?"
                    ],
                    "closing": "Thank you for considering BuildPro for your project. We'll send over the detailed estimate by tomorrow evening. Is this the best number to reach you if we have any follow-up questions?"
                },
                "Schedule Consultation": {
                    "introduction": f"Hi, this is Mike from BuildPro Construction. I'm reaching out about the {context} you're interested in. Thanks for your interest in our services!",
                    "main_points": [
                        "We'd love to schedule a free consultation to discuss your project",
                        "Our experts can provide on-site assessment and recommendations",
                        "We bring 15+ years of experience in quality construction",
                        "All consultations come with no obligation"
                    ],
                    "questions": [
                        "What days and times work best for you this week?",
                        "Are you the primary decision maker, or should others be present?",
                        "How soon are you looking to get started with the project?",
                        "Do you have any initial questions about our services?"
                    ],
                    "closing": "Great! I'll put you down for that appointment. We'll send a confirmation text with our consultant's contact information. Looking forward to helping you with this project!"
                },
                "Payment Reminder": {
                    "introduction": f"Hello, this is Jennifer from BuildPro Construction. I'm calling regarding the payment for your recent {context} project. I hope you're completely satisfied with the completed work!",
                    "main_points": [
                        "Your project was completed on [date] and we hope you love the results",
                        "We have an outstanding balance of $[amount] on your account",
                        "Payment was due on [due date] according to our agreement",
                        "We offer several convenient payment options"
                    ],
                    "questions": [
                        "Are you satisfied with the completed work?",
                        "Is there anything about the project that needs our attention?",
                        "What's the best way for you to process payment today?",
                        "Do you need us to resend the invoice for your records?"
                    ],
                    "closing": "Thank you for choosing BuildPro. We appreciate your business and look forward to working with you again in the future. Payment can be made online, by phone, or check."
                },
                "Project Update": {
                    "introduction": f"Hi, this is Tom from BuildPro Construction. I'm calling with an update on your {context} project. I wanted to keep you informed of our progress.",
                    "main_points": [
                        "Your project is currently [status] and progressing well",
                        "We're on track to meet the projected completion date",
                        "Our team is maintaining high quality standards throughout",
                        "Any weather delays or material changes will be communicated immediately"
                    ],
                    "questions": [
                        "Do you have any questions about the current progress?",
                        "Have you noticed any issues or concerns on-site?",
                        "Are you satisfied with the quality of work so far?",
                        "Is there anything specific you'd like us to focus on?"
                    ],
                    "closing": "Thanks for your time! We'll continue to keep you updated as we progress. Please don't hesitate to call if you have any questions or concerns."
                },
                "New Client Outreach": {
                    "introduction": f"Hello, this is Alex from BuildPro Construction. I'm reaching out because we're currently scheduling {context} projects in your area and wanted to see if you might be interested in our services.",
                    "main_points": [
                        "We specialize in high-quality construction and renovation work",
                        "We're offering free estimates for projects in your neighborhood",
                        "Our team has excellent local references and reviews",
                        "We're licensed, bonded, and fully insured"
                    ],
                    "questions": [
                        "Are you planning any construction or renovation projects?",
                        "What type of work are you most interested in?",
                        "Have you been thinking about any home improvements?",
                        "Would you be interested in a free, no-obligation estimate?"
                    ],
                    "closing": "Thank you for your time! Even if you're not ready now, please keep our contact information handy for future projects. We'd love to earn your business when the time is right."
                }
            }
            
            # Get the appropriate script template or use default
            script = script_templates.get(purpose, script_templates["New Client Outreach"])
            
            # Log outbound call attempt
            call_data = {
                'call_type': 'outbound',
                'phone_number': phone_number,
                'client_name': 'Prospect',
                'call_duration': 0,
                'call_status': 'initiated',
                'call_summary': f"Outbound call for: {purpose}. Context: {context}",
                'follow_up_required': True
            }
            
            call_id = log_ai_call(call_data)
            
            return {
                'call_id': call_id,
                'script': script,
                'status': 'ready'
            }
        except Exception as e:
            st.error(f"Error initiating outbound call: {str(e)}")
            return None
