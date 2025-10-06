# Overview

PLANDEPA is a comprehensive building management dashboard designed for construction and renovation businesses - Build Smart, Grow Simple. The application provides a complete business management solution including customer relationship management (CRM), project estimation, job tracking, financial management, invoice generation, and AI-powered call analysis. Built with Streamlit, the system offers a web-based interface for managing all aspects of a construction business from lead generation through project completion.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit-based web application with custom CSS styling
- **UI Pattern**: Multi-page application with tab-based navigation within each page
- **Styling**: Custom CSS with professional building industry theme, animated backgrounds, and responsive design
- **Session Management**: Streamlit session state for user authentication and navigation state

## Backend Architecture
- **Language**: Python with modular page-based architecture
- **Database Layer**: PostgreSQL with psycopg2 driver for connection management
- **Authentication**: Custom hash-based authentication system using SHA256 password hashing
- **Authorization**: Role-based access control with three tiers (user, admin, super_admin)
- **AI Integration**: Mock AI system for call analysis and customer interaction processing

## Data Storage Solutions
- **Primary Database**: PostgreSQL with comprehensive schema including:
  - User management (users table)
  - Customer relationship management (customers, customer_contacts tables)
  - Project management (estimates, jobs tables)
  - Financial tracking (financial_records, invoices tables)
  - AI call logging (ai_calls table)
- **Connection Management**: Environment-based database configuration with connection pooling
- **Data Initialization**: Automated table creation and schema setup

## Authentication and Authorization
- **Authentication Method**: Username/password with SHA256 hashing
- **Session Management**: Streamlit session state with persistent login
- **Role Hierarchy**: Three-tier system (super_admin > admin > user)
- **Permission Checking**: Function-based permission validation for page access
- **User Management**: Admin panel for user creation and role assignment

## Core Business Modules
- **Customer Management**: Full CRM with contact history and follow-up tracking
- **Estimation System**: Quote generation with AI-assisted cost analysis
- **Job Management**: Project tracking with status updates and calendar views
- **Financial Dashboard**: Revenue tracking, expense management, and profit analysis
- **Invoice System**: Automated invoice generation with payment tracking
- **AI Caller Bot**: Mock AI system for call analysis and customer interaction processing

# External Dependencies

## Required Python Packages
- **streamlit**: Web application framework and UI components
- **psycopg2**: PostgreSQL database adapter and connection management
- **plotly**: Interactive charts and data visualization components
- **pandas**: Data manipulation and analysis for reporting features
- **hashlib**: Password hashing and security functions (Python standard library)

## Database Requirements
- **PostgreSQL**: Primary database system for all application data
- **Environment Variables**: Database connection configured via PGHOST, PGDATABASE, PGUSER, PGPASSWORD, PGPORT

## AI Services
- **Current Implementation**: Mock AI system with simulated responses
- **Future Integration**: Designed to support OpenAI API integration for real call analysis
- **Call Processing**: Intent analysis, urgency assessment, and action recommendation

## External Service Integrations
- **Email System**: Ready for SMTP integration for automated notifications
- **Calendar Services**: Designed for integration with external calendar systems
- **Payment Processing**: Invoice system prepared for payment gateway integration
- **Phone/VoIP Services**: AI caller system designed for telephony API integration

## Environment Configuration
- **Database Connection**: PostgreSQL connection via environment variables
- **Authentication**: No external OAuth providers (custom implementation)
- **File Storage**: Local file system (ready for cloud storage integration)
- **Logging**: Database-based logging for AI calls and user activities