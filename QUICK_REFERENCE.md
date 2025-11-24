# Quick Reference Guide

## 🔐 Login Credentials

**Super Admin:**
- Email: `waheedkals@yahoo.com`
- Password: `K@lwars98`

## 📍 Page Locations

| Feature | URL | Description |
|---------|-----|-------------|
| Login | `/login` | User authentication |
| Dashboard | `/dashboard` | Overview and metrics |
| Jobs | `/jobs` | List all scraping jobs |
| New Job | `/jobs/new` | Create scraping job |
| Leads | `/leads` | Manage all leads |
| Templates | `/templates` | Email templates |
| New Template | `/templates/new` | Create template |
| Admin Users | `/admin/users` | User management (Admin only) |
| Admin Activity | `/admin/activity` | Activity logs (Admin only) |
| Admin Health | `/admin/health` | System health (Admin only) |
| Settings | `/settings` | Account settings |

## 🚀 Quick Actions

### Create a Scrape Job
1. Go to `/jobs/new`
2. Enter niche (e.g., "dentist clinic")
3. Enter location (optional)
4. Set max results (default: 20)
5. Select data sources
6. Choose extraction options
7. Click "Create Job"

### Find Leads
1. Go to `/leads`
2. Use search bar or filters
3. Click lead to view details
4. Export if needed

### Create Template
1. Go to `/templates/new`
2. Enter name and description
3. Choose template type
4. Write content (use `{{variables}}`)
5. Add tags
6. Click "Create Template"

## 📊 Health Score Guide

| Score | Grade | Quality |
|-------|-------|---------|
| 90-100 | A | Excellent |
| 80-89 | B | Good |
| 70-79 | C | Average |
| 60-69 | D | Below Average |
| 0-59 | F | Poor |

## 🎯 Job Statuses

- **Queued**: Waiting to start
- **Running**: Currently processing
- **Completed**: Finished successfully
- **Failed**: Error occurred
- **AI Processing**: Enrichment in progress

## 📝 Template Variables

Use these in templates:
- `{{first_name}}` - Contact's first name
- `{{company_name}}` - Company name
- `{{website}}` - Website URL
- `{{email}}` - Email address
- `{{sender_name}}` - Your name

## ⚙️ Common Settings

### Job Settings
- **Max Results**: 20-50 recommended
- **Max Pages**: 3-5 recommended
- **Sources**: Enable Google Search + Crawling

### Data Extraction
- ✅ Emails
- ✅ Phones
- ✅ Social Links
- ✅ Services

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't login | Check credentials, verify account status |
| Job not starting | Check settings, verify API keys |
| No leads found | Try different keywords, adjust location |
| Low scores | Enable crawling, check sources |

## 📞 Support

- Check USER_MANUAL.md for detailed help
- Contact your administrator
- Review error messages

---

*For complete documentation, see USER_MANUAL.md*

