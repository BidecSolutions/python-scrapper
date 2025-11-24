# How to Use All Features - Step-by-Step Guide

This guide provides practical, step-by-step instructions for using every feature in the Lead Scraper platform.

---

## 🚀 Getting Started

### Step 1: Login

1. Open your browser and go to: `http://localhost:3001` (or your server URL)
2. You'll be redirected to `/login`
3. Enter credentials:
   - **Email**: `waheedkals@yahoo.com`
   - **Password**: `K@lwars98`
4. Click "Sign in"
5. You'll be taken to the Dashboard

---

## 📊 Dashboard - Understanding Your Overview

### What You See

1. **Metrics Cards** (Top row):
   - Total Leads: All leads in your database
   - Leads This Month: New leads this month
   - Month Change: % change from last month
   - Average Lead Score: Average quality score
   - AI Enriched %: Percentage with AI data

2. **Health Score Section**:
   - Average health score
   - Score distribution by grade
   - Recommendations

3. **Recent Jobs**:
   - Your latest scraping jobs
   - Status and results

### How to Use

- **View Job Details**: Click any job in "Recent Jobs"
- **Create New Job**: Click "New Scrape Job" button
- **View All Jobs**: Click "View All Jobs"
- **View All Leads**: Click "View All Leads"

---

## 🔍 Jobs - Finding Leads

### Creating Your First Scrape Job

#### Example: Find Dentist Clinics in Karachi

1. **Navigate to New Job**:
   - Click "New Scrape Job" from dashboard, OR
   - Go to `/jobs/new`

2. **Fill Basic Information**:
   ```
   Niche: dentist clinic
   Location: Karachi
   Max Results: 20
   Max Pages Per Site: 5
   ```

3. **Select Data Sources**:
   - ✅ Check "Google Custom Search" (always recommended)
   - ⬜ "Google Places" (needs API key)
   - ⬜ "Web Search (Bing)" (needs API key)
   - ✅ Check "Website Crawling" (for enrichment)

4. **Choose What to Extract**:
   - ✅ Email addresses
   - ✅ Phone numbers
   - ✅ Services / Categories
   - ✅ Social media links
   - ✅ Contacts from social pages
   - ⬜ Full website content (optional)

5. **Create Job**:
   - Click "Create Job" button
   - You'll be redirected to job detail page

### Monitoring Job Progress

1. **On Job Detail Page** (`/jobs/{id}`):
   - See real-time status
   - Watch progress updates
   - View leads as they're found

2. **Job Statuses**:
   - **Queued**: Waiting to start
   - **Running**: Currently scraping
   - **Completed**: Finished successfully
   - **Failed**: Error occurred

3. **View Results**:
   - Scroll down to "Leads" section
   - See all discovered leads
   - Click any lead for details

### Viewing All Jobs

1. Go to `/jobs`
2. **Filter Jobs**:
   - Use status dropdown: All, Running, Completed, Failed
   - Use search bar to find specific jobs
3. **View Job Details**: Click any job row
4. **View Job Leads**: Click job, then scroll to leads section

### Best Practices for Jobs

**Example Scenarios:**

**Scenario 1: Local Business Search**
```
Niche: restaurant
Location: Dubai
Max Results: 30
Sources: Google Search + Crawling
Extract: Emails, Phones, Social Links
```

**Scenario 2: Global Search**
```
Niche: software development company
Location: (leave empty)
Max Results: 50
Sources: Google Search + Crawling
Extract: All options enabled
```

**Scenario 3: Quick Test**
```
Niche: law firm
Location: London
Max Results: 10
Sources: Google Search only
Extract: Emails, Phones
```

---

## 👥 Leads - Managing Your Discovered Leads

### Viewing All Leads

1. Go to `/leads`
2. **Default View**: Shows all leads in your database

### Searching Leads

**Method 1: Quick Search**
- Type in search bar: "dentist", "Karachi", "email@example.com"
- Results update automatically

**Method 2: Advanced Filters**
- **Source Filter**: Select data source (Google, Bing, etc.)
- **Quality Filter**: High, Medium, Low, or All
- **Score Range**: Set min/max health score

**Method 3: Saved Views**
- Create filter combination
- Click "Save View"
- Name your view (e.g., "High Quality Leads")
- Click saved view to apply filters instantly

### Viewing Lead Details

1. **Click any lead** in the table
2. **Detail Panel Opens** showing:
   - Complete contact information
   - Health score breakdown
   - Enrichment data (tech stack, social links)
   - Activity history

### Exporting Leads

**Option 1: Export All**
1. Click "Export" button (top right)
2. Choose format (CSV)
3. Download file

**Option 2: Export Filtered**
1. Apply your filters
2. Click "Export"
3. Only filtered leads exported

**Option 3: Export Selected**
1. Check boxes next to leads
2. Click "Export Selected"
3. Only selected leads exported

### Understanding Health Scores

**Score Calculation:**
- Email present: +20 points
- Phone present: +20 points
- Website present: +15 points
- Address present: +15 points
- Recently updated: +15 points
- No bounce flags: +15 points

**What to Do:**
- **Score 90-100 (A)**: Excellent, ready to use
- **Score 80-89 (B)**: Good quality, minor improvements possible
- **Score 70-79 (C)**: Average, may need verification
- **Score 60-69 (D)**: Below average, verify before use
- **Score 0-59 (F)**: Poor, needs significant improvement

**Improving Scores:**
- Enable website crawling in jobs
- Use multiple data sources
- Re-run jobs with better settings

---

## 📧 Templates - Email Templates

### Creating Your First Template

#### Example: Cold Outreach Template

1. **Go to Templates**: `/templates`
2. **Click "New Template"**
3. **Fill Basic Info**:
   ```
   Name: Cold Outreach - SaaS Companies
   Description: Initial outreach for SaaS businesses
   Type: Email
   Scope: Workspace
   ```

4. **Write Subject Line**:
   ```
   Quick question about {{company_name}}
   ```

5. **Write Email Body**:
   ```
   Hi {{first_name}},

   I noticed that {{company_name}} is in the {{niche}} space.

   I'd love to share how we've helped similar companies...

   Best regards,
   {{sender_name}}
   ```

6. **Add Tags**:
   - Type "cold-outreach" and press Enter
   - Type "saas" and press Enter
   - Type "initial" and press Enter

7. **Create Template**:
   - Click "Create Template"
   - Status will be "Draft"

### Using Variables in Templates

**Available Variables:**
- `{{first_name}}` - Contact's first name
- `{{last_name}}` - Contact's last name
- `{{company_name}}` - Company name
- `{{website}}` - Website URL
- `{{email}}` - Email address
- `{{niche}}` - Business niche
- `{{sender_name}}` - Your name
- `{{sender_email}}` - Your email

**Example Template:**
```
Subject: Partnership opportunity for {{company_name}}

Body:
Hello {{first_name}},

I came across {{company_name}} ({{website}}) and noticed you're in the {{niche}} industry.

We specialize in helping companies like yours...

Looking forward to connecting!

{{sender_name}}
{{sender_email}}
```

### Managing Templates

1. **View Templates**: Go to `/templates`
2. **Filter by Status**:
   - All: See everything
   - Draft: Your work in progress
   - Pending: Awaiting approval
   - Approved: Ready to use
3. **View Template**: Click any template
4. **Approve/Reject** (Admin only): Use action buttons

### Template Workflow

1. **Create** → Status: Draft
2. **Submit for Approval** → Status: Pending
3. **Admin Reviews** → Status: Approved or Rejected
4. **Use Approved Templates** in your campaigns

---

## 👨‍💼 Admin Features (Super Admin Only)

### Managing Users

#### View All Users

1. Go to `/admin/users`
2. **See User List**:
   - Email and name
   - Status (Active, Pending, Suspended)
   - Permissions
   - Creation date
   - Last login

#### Create New User

1. Click "Create User" button
2. **Fill Form**:
   ```
   Email: user@example.com
   Password: SecurePassword123
   Full Name: John Doe
   Status: Pending (or Active)
   Super Admin: (uncheck for regular user)
   Advanced Features: (check if needed)
   ```
3. Click "Create User"

#### Approve Pending Users

1. Find user with "Pending" status
2. Click "Approve" button
3. User status changes to "Active"
4. User can now log in

#### Suspend Users

1. Find active user
2. Click "Suspend" button
3. User status changes to "Suspended"
4. User cannot log in

#### Edit User Permissions

1. Find user in list
2. **Toggle Checkboxes**:
   - "Advanced": Enable advanced features
   - "Super Admin": Grant admin access
3. Changes save automatically

### Monitoring Activity

1. Go to `/admin/activity`
2. **View Global Activity**:
   - All actions across all workspaces
   - User actions
   - System events
3. **Filter Activity**:
   - Workspace ID: Filter by workspace
   - User ID: Filter by user
   - Type: Filter by activity type
4. **Activity Types**:
   - Lead created/updated
   - Email found/verified
   - Job created/completed
   - Template actions
   - User actions

### System Health Monitoring

1. Go to `/admin/health`
2. **View Summary Metrics**:
   - Average health score
   - Total workspaces
   - Healthy/Warning/Critical counts
3. **Workspace Details**:
   - Health score per workspace
   - Bounce rate
   - Failed jobs (7 days)
   - LinkedIn failure rate
4. **Take Action**:
   - Identify workspaces with low scores
   - Check failed jobs
   - Address issues

---

## 🎯 Additional Features

### Deals Management

1. Go to `/deals`
2. **Create Deal**:
   - Click "New Deal"
   - Associate with lead
   - Set deal value
   - Track stages
3. **Manage Pipeline**:
   - View all deals
   - Update status
   - Track progress

### Duplicate Detection

1. Go to `/duplicates`
2. **View Duplicates**:
   - See detected duplicate groups
   - Review similarity scores
3. **Merge Duplicates**:
   - Select duplicates to merge
   - Choose primary record
   - Merge data

### Health Monitoring

1. Go to `/health`
2. **View Health Metrics**:
   - Overall health score
   - Quality distribution
   - Recommendations
3. **Improve Health**:
   - Follow recommendations
   - Enable better data sources
   - Update lead information

### Email Verification

1. Go to `/verification`
2. **Verify Leads**:
   - View verification status
   - Run verification jobs
   - See verification results
3. **Filter by Status**:
   - Verified
   - Unverified
   - Invalid

### Email Finder

1. Go to `/email-finder`
2. **Find Emails**:
   - Enter company name
   - Search for contacts
   - Verify email addresses
3. **Export Results**:
   - Download email list
   - Export verified emails

### Lookalike Audiences

1. Go to `/lookalike`
2. **Create Lookalike Job**:
   - Select source segment/list
   - Define criteria
   - Start job
3. **View Results**:
   - See similar companies
   - Review match scores
   - Export lookalikes

### Playbooks (Automation)

1. Go to `/playbooks`
2. **Create Playbook**:
   - Define trigger conditions
   - Set actions
   - Configure workflow
3. **Run Playbooks**:
   - Manual execution
   - Scheduled runs
   - Event-triggered

### Robots (AI Automation)

1. Go to `/robots`
2. **Create Robot**:
   - Define scraping rules
   - Set extraction schema
   - Configure workflow
3. **Use Robots**:
   - Run on websites
   - Extract custom data
   - Automate workflows

### Settings

1. Go to `/settings`
2. **Profile Settings**:
   - Update email
   - Change password
   - Update name
3. **Organization Settings**:
   - Organization name
   - Branding
   - Plan details
4. **API Keys**:
   - View keys
   - Generate new keys
   - Revoke keys
5. **Notifications**:
   - Email preferences
   - In-app notifications
   - Alert settings

---

## 🔄 Common Workflows

### Workflow 1: Find and Export High-Quality Leads

1. **Create Job**:
   - Niche: "restaurant"
   - Location: "New York"
   - Enable all data sources
   - Enable all extraction options

2. **Wait for Completion**:
   - Monitor job progress
   - Wait for "Completed" status

3. **Filter Leads**:
   - Go to `/leads`
   - Set quality filter: "High"
   - Set score range: 80-100

4. **Export**:
   - Click "Export"
   - Download CSV file

### Workflow 2: Create and Use Email Template

1. **Create Template**:
   - Go to `/templates/new`
   - Write template with variables
   - Save as draft

2. **Submit for Approval**:
   - Change status to "Pending"
   - Admin approves

3. **Use Template**:
   - Copy template content
   - Replace variables with lead data
   - Send personalized emails

### Workflow 3: Admin - Onboard New User

1. **Create User**:
   - Go to `/admin/users`
   - Click "Create User"
   - Fill user details
   - Set status: "Pending"

2. **Notify User**:
   - Share login credentials
   - Provide access URL

3. **Approve User**:
   - User attempts login
   - Admin approves from `/admin/users`
   - User gains access

### Workflow 4: Monitor System Health

1. **Check Dashboard**:
   - View health score metrics
   - Review recommendations

2. **Check Admin Health**:
   - Go to `/admin/health`
   - Review workspace health
   - Identify issues

3. **Take Action**:
   - Address low scores
   - Fix failed jobs
   - Improve data sources

---

## 💡 Pro Tips

### For Better Lead Quality

1. **Use Specific Niches**:
   - ❌ "business"
   - ✅ "digital marketing agency"

2. **Enable Website Crawling**:
   - Always check "Website Crawling"
   - Gets more complete data

3. **Use Multiple Sources**:
   - Google Search (always)
   - Google Places (if available)
   - Website Crawling (always)

### For Better Job Performance

1. **Start Small**:
   - Test with 10-20 results first
   - Then scale up

2. **Optimize Pages**:
   - 3-5 pages per site is optimal
   - More pages = slower but more data

3. **Monitor Jobs**:
   - Check job status regularly
   - Review failed jobs

### For Template Management

1. **Use Variables**:
   - Always use `{{variables}}` for personalization
   - Test templates before approval

2. **Organize with Tags**:
   - Tag by purpose: "cold-outreach", "follow-up"
   - Tag by industry: "saas", "healthcare"

3. **Version Control**:
   - Deprecate old templates
   - Create new versions

### For Admin Tasks

1. **Regular Monitoring**:
   - Check activity logs daily
   - Review system health weekly

2. **User Management**:
   - Approve users promptly
   - Review permissions regularly

3. **System Maintenance**:
   - Address health issues quickly
   - Monitor failed jobs

---

## ❓ Troubleshooting

### Job Not Starting

**Problem**: Job stays in "Queued" status

**Solutions**:
1. Check job settings
2. Verify API keys (if using Google Places/Bing)
3. Check system health
4. Try creating new job

### No Leads Found

**Problem**: Job completes but finds 0 leads

**Solutions**:
1. Try different niche keywords
2. Remove location filter
3. Increase max results
4. Check data source settings

### Low Health Scores

**Problem**: Leads have low scores (below 70)

**Solutions**:
1. Enable website crawling
2. Use multiple data sources
3. Increase max pages per site
4. Re-run jobs with better settings

### Can't Login

**Problem**: Login fails

**Solutions**:
1. Verify email and password
2. Check account status (may be pending)
3. Contact admin for approval
4. Try password reset (if available)

### Template Not Working

**Problem**: Variables not replacing

**Solutions**:
1. Check variable syntax: `{{variable_name}}`
2. Ensure variable names match available fields
3. Test template with sample data
4. Review template documentation

---

## 📚 Next Steps

1. **Explore Features**: Try each feature to understand capabilities
2. **Create Test Jobs**: Start with small jobs to learn
3. **Build Templates**: Create templates for your use cases
4. **Monitor Health**: Keep an eye on system health
5. **Read Full Manual**: See `USER_MANUAL.md` for detailed info

---

## 🎓 Learning Path

### Day 1: Basics
- ✅ Login and explore dashboard
- ✅ Create your first job
- ✅ View leads

### Day 2: Management
- ✅ Filter and search leads
- ✅ Export leads
- ✅ Understand health scores

### Day 3: Templates
- ✅ Create first template
- ✅ Use variables
- ✅ Manage templates

### Day 4: Advanced
- ✅ Use saved views
- ✅ Bulk operations
- ✅ Advanced filters

### Day 5: Admin (if applicable)
- ✅ User management
- ✅ Activity monitoring
- ✅ System health

---

**Remember**: Start simple, then explore advanced features as you become comfortable!

For detailed information, refer to `USER_MANUAL.md`  
For quick reference, see `QUICK_REFERENCE.md`

