# Lead Scraper - Complete User Manual

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Authentication & Login](#authentication--login)
4. [Dashboard](#dashboard)
5. [Jobs - Lead Scraping](#jobs---lead-scraping)
6. [Leads Management](#leads-management)
7. [Templates](#templates)
8. [Admin Features](#admin-features)
9. [Additional Features](#additional-features)
10. [Settings](#settings)
11. [Tips & Best Practices](#tips--best-practices)

---

## Introduction

**Lead Scraper** is a comprehensive SaaS platform for finding, scraping, and managing business leads. It helps you discover businesses, extract contact information, enrich data, and manage your lead pipeline all in one place.

### Key Capabilities

- 🔍 **Multi-Source Lead Discovery**: Find leads from Google Custom Search, Google Places, Bing Search, and website crawling
- 📊 **Data Enrichment**: Automatically extract emails, phones, social links, tech stack, and more
- 📈 **Health Scoring**: Get quality scores for your leads (0-100)
- 🎯 **Lead Management**: Organize, filter, and track your leads
- 📧 **Template Library**: Create and manage email templates
- 👥 **User Management**: Multi-user collaboration with role-based access
- 📊 **Analytics**: Track performance, usage, and system health

---

## Getting Started

### Prerequisites

- A web browser (Chrome, Firefox, Safari, or Edge)
- Internet connection
- Admin credentials (provided by your administrator)

### First-Time Setup

1. **Access the Application**
   - Open your browser and navigate to the application URL (e.g., `http://localhost:3001`)
   - You'll be redirected to the login page

2. **Login**
   - Enter your email and password
   - Click "Sign in"
   - If your account is pending approval, contact your administrator

3. **Explore the Dashboard**
   - After login, you'll see the main dashboard
   - Familiarize yourself with the sidebar navigation

---

## Authentication & Login

### Login Process

1. Navigate to the login page (`/login`)
2. Enter your credentials:
   - **Email**: Your registered email address
   - **Password**: Your account password
3. Click "Sign in"
4. You'll be redirected to the dashboard upon successful login

### Account Status

Your account can have one of three statuses:

- **Active**: Full access to all features
- **Pending**: Awaiting admin approval (limited access)
- **Suspended**: Account temporarily disabled (contact admin)

### Logout

- Click the "Logout" button in the top-right corner
- You'll be redirected to the login page

### Super Admin Access

Super admins have access to:
- User management (`/admin/users`)
- Global activity logs (`/admin/activity`)
- System health monitoring (`/admin/health`)

**Default Super Admin Credentials:**
- Email: `waheedkals@yahoo.com`
- Password: `K@lwars98`

---

## Dashboard

The dashboard provides an overview of your lead generation activities and key metrics.

### Dashboard Overview

**Location**: `/dashboard`

### Key Metrics Displayed

1. **Total Leads**: Total number of leads in your database
2. **Leads This Month**: Number of leads scraped this month
3. **Month Change**: Percentage change from last month
4. **Average Lead Score**: Average health score across all leads
5. **AI Enriched %**: Percentage of leads enriched with AI

### Health Score Statistics

- **Average Health Score**: Overall quality of your leads
- **Score Distribution**: Breakdown by grade (A, B, C, D, F)
- **Recommendations**: Suggestions to improve lead quality

### Recent Jobs

- List of your most recent scraping jobs
- Shows job status, niche, location, and result count
- Click any job to view details

### Quick Actions

- **New Scrape Job**: Create a new lead scraping job
- **View All Jobs**: Navigate to the jobs page
- **View All Leads**: Navigate to the leads page

---

## Jobs - Lead Scraping

Jobs are the core feature for discovering and scraping leads from various sources.

### Creating a New Job

**Location**: `/jobs/new`

#### Step 1: Basic Information

1. **Niche** (Required)
   - Enter the type of business you're looking for
   - Examples: "dentist clinic", "restaurant", "hospital", "law firm"
   - Be specific for better results

2. **Location** (Optional)
   - Enter a city, state, or country
   - Examples: "Karachi", "London", "Dubai", "New York"
   - Leave empty to search globally

3. **Max Results**
   - Maximum number of leads to find (default: 20)
   - Range: 1-500
   - Higher numbers take longer but provide more leads

4. **Max Pages Per Site**
   - How many pages to crawl per website (default: 5)
   - Range: 1-20
   - More pages = more data but slower processing

#### Step 2: Data Sources

Select which sources to use for finding leads:

- ✅ **Google Custom Search** (Recommended)
  - Uses Google's search engine to find businesses
  - No API key required
  - Fast and reliable

- ⚠️ **Google Places** (Requires API Key)
  - Finds businesses from Google Maps/Places
  - Requires Google Places API key
  - Great for local businesses

- ⚠️ **Web Search (Bing)** (Requires API Key)
  - Uses Bing Search API
  - Requires Bing Search API key
  - Alternative to Google

- ✅ **Website Crawling** (Enrichment)
  - Crawls found websites to extract additional data
  - Enriches leads with emails, phones, social links
  - Recommended for complete data

#### Step 3: Data Extraction

Choose what information to collect:

- ✅ **Email addresses**: Extract email contacts
- ✅ **Phone numbers**: Extract phone numbers
- ✅ **Services / Categories**: Identify business services
- ✅ **Social media links**: Find Facebook, LinkedIn, Twitter, etc.
- ✅ **Contacts from social pages**: Extract contacts from social profiles
- ⬜ **Full website content**: Download entire website text (optional)

#### Step 4: Create Job

1. Review your settings
2. Click "Create Job"
3. You'll be redirected to the job detail page to monitor progress

### Viewing Jobs

**Location**: `/jobs`

#### Job List Features

- **Status Filter**: Filter by All, Running, Completed, Failed
- **Search**: Search jobs by niche or location
- **Sorting**: Jobs are sorted by creation date (newest first)

#### Job Statuses

- **Queued**: Job is waiting to start
- **Running**: Job is currently processing
- **Completed**: Job finished successfully
- **Failed**: Job encountered an error
- **AI Processing**: AI enrichment in progress
- **Completed (Warnings)**: Finished with some issues

#### Job Metrics

Each job shows:
- **Status**: Current job state
- **Niche & Location**: What was searched
- **Results**: Number of leads found
- **Created**: When the job was created
- **Duration**: How long it took

### Job Details

**Location**: `/jobs/{id}`

#### Job Information

- Complete job details
- Status and progress
- Quality statistics (high/medium/low quality leads)
- Performance metrics

#### Job Leads

- Full table of all leads from the job
- Filterable and sortable
- Export options
- Click any lead to view details

---

## Leads Management

The leads page is where you manage all your discovered leads.

### Leads Page

**Location**: `/leads`

### Features

#### 1. Search & Filters

- **Search Bar**: Search by name, email, website, or niche
- **Source Filter**: Filter by data source (Google, Bing, etc.)
- **Quality Filter**: Filter by quality (All, High, Medium, Low)
- **Score Range**: Filter by health score range
- **Saved Views**: Save and reuse filter combinations

#### 2. Lead Table

Columns displayed:
- **Name**: Business name
- **Niche**: Business type
- **Website**: Business website URL
- **Email**: Extracted email addresses
- **Phone**: Extracted phone numbers
- **Score**: Health score (0-100)
- **Source**: Where the lead was found
- **Tags**: Custom tags
- **Actions**: View details, export, etc.

#### 3. Bulk Actions

- Select multiple leads
- Bulk export
- Bulk tag assignment
- Bulk status changes

#### 4. Export Options

- **CSV Export**: Download leads as CSV file
- **Filtered Export**: Export only filtered leads
- **Selected Export**: Export only selected leads

### Lead Details Panel

Click any lead to open the detail panel showing:

- **Full Information**:
  - Complete contact details
  - Address and location
  - Social media links
  - Tech stack detected
  - Services/categories

- **Health Score Details**:
  - Score breakdown
  - Grade (A-F)
  - Recommendations for improvement

- **Enrichment Data**:
  - AI-generated insights
  - Company size estimation
  - Contact person information

- **Activity History**:
  - When the lead was created
  - Last updated
  - Related jobs

### Health Score

Each lead has a health score (0-100) based on:

- **Email Present**: +20 points
- **Phone Present**: +20 points
- **Website Present**: +15 points
- **Address Present**: +15 points
- **Recently Updated**: +15 points
- **No Bounce Flags**: +15 points

**Grades:**
- **A (90-100)**: Excellent quality
- **B (80-89)**: Good quality
- **C (70-79)**: Average quality
- **D (60-69)**: Below average
- **F (0-59)**: Poor quality

---

## Templates

Templates help you maintain consistent messaging across your team.

### Template Library

**Location**: `/templates`

### Template Types

1. **Email Templates**: Full email body templates
2. **Subject Line Templates**: Email subject templates
3. **Sequence Step Templates**: Templates for email sequences

### Template Statuses

- **Draft**: Work in progress
- **Pending**: Awaiting approval
- **Approved**: Ready to use
- **Deprecated**: No longer in use
- **Rejected**: Not approved

### Creating a Template

**Location**: `/templates/new`

#### Step 1: Basic Information

- **Template Name** (Required): Descriptive name
- **Description**: When and how to use this template
- **Template Type**: Email, Subject, or Sequence Step
- **Scope**: Workspace (team) or Global (all users)

#### Step 2: Email Content (for Email Templates)

- **Subject Line**: Email subject (supports variables)
- **Email Body** (Required): Email content
  - Use `{{variable_name}}` for dynamic content
  - Examples: `{{first_name}}`, `{{company_name}}`, `{{sender_name}}`

#### Step 3: Tags

- Add tags to organize templates
- Press Enter after typing a tag
- Remove tags by clicking the × button

#### Step 4: Create

- Review your template
- Click "Create Template"
- Template will be saved as "Draft" status

### Managing Templates

#### Filtering

- **All**: Show all templates
- **Draft**: Show draft templates
- **Pending**: Show pending approval
- **Approved**: Show approved templates

#### Actions

- **View**: See full template details
- **Approve** (Admin): Approve pending templates
- **Reject** (Admin): Reject pending templates

### Using Variables

Templates support dynamic variables:

- `{{first_name}}`: Contact's first name
- `{{last_name}}`: Contact's last name
- `{{company_name}}`: Company name
- `{{website}}`: Company website
- `{{email}}`: Contact email
- `{{sender_name}}`: Your name
- `{{sender_email}}`: Your email

---

## Admin Features

Admin features are available to super admin users only.

### User Management

**Location**: `/admin/users`

#### Features

1. **View All Users**
   - See all users in the system
   - Filter by status (All, Active, Pending, Suspended)
   - Search by email or name

2. **User Information**
   - Email and full name
   - Account status
   - Permissions (Advanced features, Super Admin)
   - Creation date and last login

3. **User Actions**
   - **Approve**: Activate pending users
   - **Suspend**: Temporarily disable users
   - **Reject**: Reject pending users
   - **Edit Permissions**: Toggle advanced features and super admin status

4. **Create New User**
   - Click "Create User" button
   - Fill in user details:
     - Email (required)
     - Password (required, min 8 characters)
     - Full Name (optional)
     - Status (Pending, Active, Suspended)
     - Permissions (Super Admin, Advanced Features)

#### User Statuses

- **Active**: User can log in and use the system
- **Pending**: User account created but awaiting approval
- **Suspended**: User account temporarily disabled

### Activity Logs

**Location**: `/admin/activity`

#### Features

1. **Global Activity View**
   - See all activity across all workspaces
   - Filter by workspace, user, or activity type
   - Real-time activity monitoring

2. **Activity Types**
   - Lead created/updated
   - Email found/verified
   - Campaign events
   - Job created/completed/failed
   - Template actions
   - User actions

3. **Filters**
   - **Workspace ID**: Filter by specific workspace
   - **User ID**: Filter by specific user
   - **Activity Type**: Filter by event type

4. **Activity Details**
   - Timestamp (relative and absolute)
   - Workspace information
   - User who performed the action
   - Activity metadata

### System Health

**Location**: `/admin/health`

#### Features

1. **Workspace Health Overview**
   - Average health score across all workspaces
   - Total workspaces count
   - Health status breakdown (Healthy, Warning, Critical)

2. **Workspace Metrics**
   - **Health Score**: Overall quality (0-100)
   - **Bounce Rate**: Email bounce percentage
   - **Jobs Failed (7d)**: Failed jobs in last 7 days
   - **LinkedIn Failure Rate**: LinkedIn scraping failure rate

3. **Health Status**
   - **Healthy** (80-100): Good performance
   - **Warning** (60-79): Needs attention
   - **Critical** (0-59): Requires immediate action

---

## Additional Features

### Deals

**Location**: `/deals`

Manage your sales pipeline and deals:
- Create and track deals
- Associate deals with leads
- Monitor deal stages and values
- Deal analytics and reporting

### Duplicates

**Location**: `/duplicates`

Find and manage duplicate leads:
- Automatic duplicate detection
- Merge duplicate records
- Review duplicate groups
- Prevent data redundancy

### Health

**Location**: `/health`

Monitor lead quality and system health:
- Health score statistics
- Quality metrics
- Recommendations for improvement
- Performance tracking

### Verification

**Location**: `/verification`

Verify and validate leads:
- Email verification status
- Phone verification
- Website validation
- Data quality checks

### Email Finder

**Location**: `/email-finder`

Find email addresses for leads:
- Search by company name
- Find contact emails
- Verify email addresses
- Export email lists

### Lookalike

**Location**: `/lookalike`

Find similar leads:
- Create lookalike audiences
- Find similar companies
- Expand your lead database
- AI-powered matching

### Playbooks

**Location**: `/playbooks`

Automated workflows:
- Create automation playbooks
- Define workflow steps
- Trigger actions based on events
- Streamline processes

### Robots

**Location**: `/robots`

AI-powered automation:
- Create custom robots
- Define scraping rules
- Automated data extraction
- Custom workflows

### Settings

**Location**: `/settings`

Configure your account and preferences:
- Profile settings
- Organization settings
- API keys management
- Notification preferences
- Security settings

---

## Settings

### Profile Settings

- Update your email
- Change password
- Update full name
- Profile picture

### Organization Settings

- Organization name
- Branding (logo, colors)
- Plan and billing
- Usage limits

### API Keys

- View API keys
- Generate new keys
- Revoke keys
- Set rate limits

### Notifications

- Email notifications
- In-app notifications
- Notification preferences
- Alert settings

---

## Tips & Best Practices

### Lead Scraping

1. **Be Specific with Niches**
   - Use specific terms: "orthopedic surgeon" instead of "doctor"
   - Include location for better results
   - Combine multiple niches in separate jobs

2. **Optimize Job Settings**
   - Start with 20-50 max results to test
   - Use 3-5 pages per site for balance
   - Enable website crawling for enrichment

3. **Data Sources**
   - Use Google Custom Search (no API key needed)
   - Add Google Places for local businesses
   - Enable crawling for complete data

### Lead Management

1. **Use Filters Effectively**
   - Save common filter combinations
   - Filter by quality score for best leads
   - Use tags to organize leads

2. **Health Scores**
   - Focus on leads with score 70+
   - Review recommendations to improve scores
   - Regularly update lead information

3. **Export Strategy**
   - Export filtered leads for campaigns
   - Use CSV for CRM imports
   - Export regularly to backup data

### Templates

1. **Template Best Practices**
   - Use variables for personalization
   - Keep templates concise
   - Test templates before approval
   - Organize with tags

2. **Approval Workflow**
   - Submit templates for approval
   - Review pending templates regularly
   - Deprecate outdated templates

### Admin Management

1. **User Management**
   - Approve users promptly
   - Set appropriate permissions
   - Monitor user activity
   - Suspend inactive accounts

2. **System Monitoring**
   - Check system health regularly
   - Monitor activity logs
   - Review failed jobs
   - Address critical issues quickly

### Security

1. **Password Security**
   - Use strong passwords (8+ characters)
   - Don't share passwords
   - Change passwords regularly

2. **API Keys**
   - Keep API keys secure
   - Rotate keys periodically
   - Revoke unused keys

3. **Access Control**
   - Grant minimum necessary permissions
   - Review user access regularly
   - Monitor admin actions

---

## Keyboard Shortcuts

- **Ctrl/Cmd + K**: Quick search
- **Esc**: Close modals/panels
- **Enter**: Submit forms
- **Tab**: Navigate between fields

---

## Troubleshooting

### Common Issues

1. **Can't Login**
   - Check email and password
   - Verify account is active
   - Contact admin if pending

2. **Job Not Starting**
   - Check job settings
   - Verify API keys (if required)
   - Check system health

3. **No Leads Found**
   - Try different niche keywords
   - Adjust location
   - Check data source settings

4. **Low Health Scores**
   - Enable website crawling
   - Check data sources
   - Review extraction settings

### Getting Help

- Check this manual first
- Review error messages
- Contact your administrator
- Check system health page

---

## Glossary

- **Lead**: A potential customer or business contact
- **Job**: A scraping task to find leads
- **Niche**: Business type or industry
- **Health Score**: Quality rating (0-100) for leads
- **Enrichment**: Adding additional data to leads
- **Template**: Reusable email or message format
- **Workspace**: Team or organization space
- **Super Admin**: Highest level administrator
- **API Key**: Authentication token for API access

---

## Appendix

### API Endpoints

For developers, the API documentation is available at:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

### Support

For technical support or questions:
- Contact your system administrator
- Check the documentation
- Review error logs

---

**Version**: 1.0  
**Last Updated**: 2025  
**Documentation**: Complete User Manual

---

*This manual covers all features of the Lead Scraper platform. For the most up-to-date information, refer to the in-app help or contact your administrator.*

