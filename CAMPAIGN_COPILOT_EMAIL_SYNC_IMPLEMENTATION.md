# AI Campaign Copilot & Email Sync Implementation

## ✅ What's Been Implemented

### 1. Database Schema

**Campaign Models (`app/core/orm_campaigns.py`):**
- `CampaignORM` - Campaign model with workspace, segment/list targeting, status
- `CampaignTemplateORM` - Email templates (subject/body variants) with AI generation flag
- `CampaignLeadORM` - Junction table with template references and outcome tracking
  - `subject_template_id` - Which subject variant was used
  - `body_template_id` - Which body variant was used
  - Outcome fields: `sent`, `opened`, `clicked`, `replied`, `bounced`, `unsubscribed`

**Email Sync Models (`app/core/orm_email_sync.py`):**
- `EmailMessageORM` - Email message log (inbound/outbound)
  - Headers: `message_id`, `in_reply_to`, `references`
  - Classification: `is_bounce`, `is_unsubscribe`, `is_reply`, `is_ooo`
  - Links: `campaign_id`, `lead_id`
- `EmailSyncConfigORM` - Configuration for email sync (BCC address, IMAP settings, OAuth)

### 2. AI Campaign Copilot Service (`app/services/ai_campaign_copilot.py`)

**Functions:**
- `generate_segment_summary()` - Create audience summary for AI prompt
- `generate_ai_templates()` - Generate subject lines and email bodies using LLM
- `get_template_performance()` - Calculate performance metrics per template variant

**Features:**
- Analyzes segment/list to understand target audience
- Generates multiple subject/body variants
- Tracks performance (open rate, click rate, reply rate) per variant
- Identifies winning combinations

### 3. Email Sync Service (`app/services/email_sync_service.py`)

**Functions:**
- `parse_email_message()` - Parse raw email into structured data
- `classify_email()` - Detect bounce, unsubscribe, reply, out-of-office
- `map_email_to_campaign_lead()` - Match email to campaign and lead
- `process_inbound_email()` - Full pipeline: parse → classify → update outcomes

**Classification Logic:**
- **Bounce**: Mailer-daemon, postmaster, SMTP error codes (5.1.1, 550)
- **Out of Office**: "Out of office", "automatic reply", "vacation"
- **Unsubscribe**: "unsubscribe", "remove me", "opt out"
- **Reply**: Has `In-Reply-To` or `References` header, not bounce/OOO

**Mapping Logic:**
1. Try custom headers (`X-Bidec-Campaign`, `X-Bidec-Lead`)
2. Try `In-Reply-To` → find original outbound message
3. Fallback: Match by email address + recent campaign

### 4. API Endpoints

**Campaign Copilot (`app/api/routes_campaign_copilot.py`):**
- `POST /api/campaigns/{id}/ai-templates` - Generate AI templates
- `GET /api/campaigns/{id}/template-stats` - Get template performance
- `GET /api/campaigns/{id}/templates` - List campaign templates

**Email Sync (`app/api/routes_email_sync.py`):**
- `GET /api/email-sync/config` - Get email sync configuration
- `POST /api/email-sync/process` - Process inbound email (webhook)
- `GET /api/email-sync/messages` - List email messages

## 🔄 Next Steps

### 1. Campaign Template Assignment

When sending emails, assign template variants:

```python
# In campaign send logic
from app.core.orm_campaigns import CampaignTemplateORM, TemplateType
import random

# Get templates
subjects = db.query(CampaignTemplateORM).filter(
    CampaignTemplateORM.campaign_id == campaign_id,
    CampaignTemplateORM.type == TemplateType.subject
).all()

bodies = db.query(CampaignTemplateORM).filter(
    CampaignTemplateORM.campaign_id == campaign_id,
    CampaignTemplateORM.type == TemplateType.body
).all()

# Assign variants (round-robin or random for A/B test)
for campaign_lead in leads_to_send:
    subject_template = random.choice(subjects) if subjects else None
    body_template = random.choice(bodies) if bodies else None
    
    campaign_lead.subject_template_id = subject_template.id if subject_template else None
    campaign_lead.body_template_id = body_template.id if body_template else None
    campaign_lead.sent = True
    campaign_lead.sent_at = datetime.utcnow()
```

### 2. Multi-Armed Bandit Optimization

Upgrade from round-robin to MAB:

```python
def select_template_bandit(subjects, bodies, campaign_id, db):
    """Select templates using epsilon-greedy or UCB"""
    # Get performance stats
    stats = get_template_performance(db, campaign)
    
    # Calculate UCB scores or use epsilon-greedy
    # Select best-performing variants with exploration
    pass
```

### 3. Email Sync Setup

**BCC Configuration:**
- Each workspace gets unique BCC address: `reply+{workspace_id}@yourdomain.com`
- User configures ESP to BCC this address
- Or use as "reply-to" address

**IMAP Polling Service (Background Worker):**
```python
# app/workers/email_sync_worker.py
import imaplib
from app.services.email_sync_service import process_inbound_email

def sync_emails_from_imap():
    """Poll IMAP inbox and process new emails"""
    config = get_email_sync_config(workspace_id)
    
    mail = imaplib.IMAP4_SSL(config.imap_host, config.imap_port)
    mail.login(config.imap_username, config.imap_password)
    mail.select(config.imap_folder)
    
    # Search for unread emails
    status, messages = mail.search(None, "UNSEEN")
    
    for msg_num in messages[0].split():
        # Fetch email
        status, msg_data = mail.fetch(msg_num, "(RFC822)")
        raw_email = msg_data[0][1]
        
        # Process
        process_inbound_email(
            db=db,
            raw_email=raw_email,
            workspace_id=config.workspace_id,
            organization_id=config.organization_id,
        )
    
    config.last_sync_at = datetime.utcnow()
    db.commit()
```

### 4. Gmail/Outlook API Integration (Future)

**Gmail API:**
- OAuth 2.0 setup
- Watch for new messages
- Webhook callback for real-time sync

**Outlook API (Microsoft Graph):**
- OAuth 2.0 setup
- Subscribe to message events
- Webhook callback

### 5. Frontend Integration

**Campaign Creation Flow:**
1. User selects segment/list
2. Click "Generate with AI" button
3. Show generated templates (editable)
4. User can edit, delete, or add manual templates
5. Save templates to campaign

**Campaign Detail Page:**
- Template performance card:
  - Table: Subject variants with open rates
  - Table: Body variants with reply rates
  - Badge: "Best subject (65% open)" / "Best body (14% reply)"
- Button: "Use winners as default"

**Email Sync Status:**
- Settings page: Show BCC address, sync status
- Campaign page: "Pulling outcomes from inbox" indicator
- Lead timeline: Show email events (sent, replied, bounced)

### 6. Auto-Optimization

**After Campaign Outcomes:**
1. Calculate performance per template
2. Identify winners
3. For future sends:
   - Gradually shift to best-performing variants
   - Use epsilon-greedy: 90% best, 10% explore
   - Or UCB: balance exploration/exploitation

**Product Feature:**
- "Auto-optimize" toggle on campaign
- System automatically adjusts template distribution
- Show optimization status: "Optimizing: 70% using Subject B"

## 📊 Usage Examples

**Generate AI Templates:**
```bash
POST /api/campaigns/1/ai-templates
{
  "num_subjects": 3,
  "num_bodies": 2,
  "tone": "friendly",
  "goal": "book intro calls",
  "offer": "Free trial of our lead platform"
}
```

**Get Template Performance:**
```bash
GET /api/campaigns/1/template-stats
```

**Response:**
```json
{
  "subjects": [
    {
      "id": 1,
      "name": "Subject A",
      "content": "Quick question about your lead gen",
      "sent": 100,
      "opened": 45,
      "open_rate": 45.0
    },
    {
      "id": 2,
      "name": "Subject B",
      "content": "How [Company] finds better leads",
      "sent": 110,
      "opened": 72,
      "open_rate": 65.45
    }
  ],
  "bodies": [
    {
      "id": 4,
      "name": "Body v1",
      "content": "...",
      "sent": 150,
      "replied": 20,
      "reply_rate": 13.33
    },
    {
      "id": 5,
      "name": "Body v2",
      "content": "...",
      "sent": 150,
      "replied": 28,
      "reply_rate": 18.67
    }
  ],
  "best_subject": { "id": 2, "name": "Subject B", ... },
  "best_body": { "id": 5, "name": "Body v2", ... }
}
```

**Process Inbound Email:**
```bash
POST /api/email-sync/process
{
  "raw_email": "From: lead@example.com\nTo: you@company.com\nSubject: Re: ...\n\nThanks for reaching out..."
}
```

## 🎯 Integration Points

**With Campaigns:**
- Templates linked to campaigns
- Variant assignment during send
- Performance tracking per variant

**With Leads:**
- Email events update lead flags (`has_replied`, `has_bounced`)
- Feed into lead scoring
- Update Next Best Action

**With Activity Timeline:**
- Log email events (sent, replied, bounced)
- Show in lead timeline
- Track rep activity

**With Segments:**
- AI uses segment context for template generation
- Performance can be analyzed per segment
- "Which templates work for US SaaS founders?"

**With Rep Performance:**
- Email outcomes feed into rep metrics
- Replies, opens, bounces attributed to rep

## ⚠️ Important Notes

1. **Template Assignment**: Implement round-robin or MAB when sending emails
2. **Email Headers**: Add `X-Bidec-Campaign` and `X-Bidec-Lead` headers to outbound emails
3. **BCC Setup**: Configure BCC address per workspace
4. **IMAP Worker**: Set up background worker to poll inbox
5. **Error Handling**: Handle email parsing errors gracefully
6. **Rate Limiting**: Respect email provider rate limits

## 🚀 Future Enhancements

- **Reply Classification**: NLP to classify reply intent (positive, neutral, negative)
- **Auto-Optimization**: Automatic template distribution based on performance
- **Template Library**: Save and reuse templates across campaigns
- **A/B Test Wizard**: Guided A/B test setup with statistical significance
- **Real-time Sync**: Gmail/Outlook webhooks for instant updates
- **Email Preview**: Show rendered templates before sending
- **Personalization**: Dynamic fields in templates ({{name}}, {{company}})
- **Send Time Optimization**: ML to predict best send times per lead

## 💡 Value Proposition

**For Users:**
- "We don't just give you leads — we help you send the *right* message"
- AI generates multiple variants, you pick the best
- System learns what works and optimizes automatically
- No more CSV imports — outcomes sync automatically

**For Managers:**
- See which messages drive replies
- Optimize campaigns based on data
- Scale what works across teams
- Full visibility into email performance

