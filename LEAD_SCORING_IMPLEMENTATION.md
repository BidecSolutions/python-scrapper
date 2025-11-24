# Lead Health Score & Next Best Action Implementation

## ✅ What's Been Implemented

### 1. Lead Health Score Service (`app/services/lead_scoring_service.py`)

**Components:**
- **Deliverability (0-30 points)**: Valid email (+30), Risky (+15), Unknown (+10), Invalid/None (+0)
- **Fit/ICP (0-40 points)**: High-performing segment (+25), Moderate segment (+15), Target role in title (+10), Target company size (+5)
- **Engagement (0-20 points)**: Replied (+20), Clicked (+10), Opened (+5), Bounced (-20 penalty)
- **Source (0-10 points)**: LinkedIn extension (+10), Company search (+7), Cleaned CSV (+5), Raw CSV (+3)

**Functions:**
- `compute_lead_score()` - Calculates 0-100 score from components
- `recompute_lead_score()` - Recomputes and saves score to lead
- Helper functions for email status, segments, campaign engagement

### 2. Next Best Action Service (`app/services/next_best_action_service.py`)

**Action Types:**
- `add_to_campaign` - High score, not recently contacted
- `schedule_follow_up` - Replied 7-30 days ago, no follow-up
- `nurture_only` - Medium score (40-69), suitable for nurture sequences
- `review_or_enrich` - Missing email or insufficient data
- `drop_or_suspend` - Bounced or suppressed

**Decision Logic:**
1. Drop/suspend if bounced or suppressed
2. Follow-up if replied 7-30 days ago
3. Add to campaign if score ≥ 70 and not contacted recently
4. Nurture if score 40-69
5. Review/enrich if missing data

**Functions:**
- `decide_next_action()` - Determines action based on context
- `recompute_next_action_for_lead()` - Recomputes and saves action

### 3. Database Schema Updates

**Added to `LeadORM`:**
- `health_score` (Numeric) - 0-100 computed score
- `health_score_last_calculated_at` (DateTime) - When score was last computed
- `next_action` (String) - Action type enum value
- `next_action_reason` (Text) - Human-readable reason
- `next_action_last_calculated_at` (DateTime) - When action was last computed

### 4. API Endpoints (`app/api/routes_lead_scoring.py`)

- `POST /api/leads/{lead_id}/recompute-score` - Recompute for single lead
- `POST /api/leads/recompute-scores` - Batch recomputation (background job)

## 🔄 Next Steps

### 1. Update Lead Schemas

Add fields to `LeadOut` / `LeadResponse`:
```python
health_score: Optional[float] = None
health_score_last_calculated_at: Optional[datetime] = None
next_action: Optional[str] = None
next_action_reason: Optional[str] = None
```

### 2. Trigger Score Recalculation

Call `recompute_lead_score()` when:
- Email verification status changes
- Campaign outcomes are imported
- Lead is added to/removed from segments
- Company enrichment updates
- Lead source changes

### 3. Frontend Integration

**Leads Table:**
- Add "Score" column with color coding:
  - 0-39: Gray (Cold)
  - 40-69: Yellow (Warm)
  - 70-100: Green (Hot)
- Add "Next Action" column with chips
- Add filters: `score >= 70`, `next_action = add_to_campaign`

**Lead Detail:**
- Show score prominently: "Score: 82 / 100 (Hot)"
- Show breakdown: Deliverability, Fit, Engagement, Source
- Show next action card with reason and action button

**Lists/Segments:**
- Show average score
- Show distribution: Hot/Warm/Cold percentages
- Show action counts: "34 leads ready for campaign"

### 4. Batch Processing

Set up periodic jobs to:
- Recompute scores for all leads (daily/weekly)
- Recompute next actions when campaign outcomes change
- Update scores when segment performance changes

### 5. Campaign Integration

When campaign outcomes are imported:
- Update `has_opened`, `has_clicked`, `has_replied`, `has_bounced` flags
- Store `last_reply_at`, `last_campaign_sent_at` in metadata
- Trigger score and NBA recalculation

## 📊 Score Calculation Example

**Lead with:**
- Valid email: +30
- In high-performing segment (reply_rate 12%): +25
- Title contains "CEO": +10
- Company size "11-50": +5
- Replied to campaign: +20
- Source: LinkedIn extension: +10

**Total: 100/100 (Hot)**

## 🎯 Next Best Action Examples

**High Score, Never Contacted:**
- Action: `add_to_campaign`
- Reason: "High score (82) and not contacted in the last 30 days."

**Replied Recently:**
- Action: `schedule_follow_up`
- Reason: "Replied 18 days ago with no recent follow-up."

**Medium Score:**
- Action: `nurture_only`
- Reason: "Medium score (55); consider adding to a low-intent or nurture sequence."

**Bounced:**
- Action: `drop_or_suspend`
- Reason: "Contact is suppressed or bounced in a previous campaign."

## 🔗 Integration Points

**With Email Verification:**
- Score updates when email status changes
- Invalid emails get 0 deliverability points

**With Segments:**
- Score uses segment performance data
- Leads in high-performing segments get fit points

**With Campaigns:**
- Engagement feeds into score
- Campaign outcomes trigger NBA updates

**With LinkedIn Extension:**
- LinkedIn leads start with higher source score
- Score adjusts as campaigns run

**With Top Segments Widget:**
- Score calculation uses segment performance
- High-scoring leads validate segment quality

## ⚠️ Important Notes

1. **Score Calculation**: Scores are computed on-demand and cached. Recompute when underlying data changes.

2. **Performance**: For large datasets, consider:
   - Background jobs for batch recalculation
   - Caching segment performance data
   - Indexing on `health_score` and `next_action`

3. **Tuning**: Adjust component weights based on your ICP and campaign performance data.

4. **Campaign Tracking**: If campaign models don't exist, the service uses metadata-based tracking as fallback.

5. **NBA Priority**: Actions are evaluated in priority order (drop → follow-up → campaign → nurture → enrich).

## 🚀 Usage Examples

**Recompute Single Lead:**
```bash
POST /api/leads/123/recompute-score
```

**Batch Recompute:**
```bash
POST /api/leads/recompute-scores
{
  "lead_ids": [1, 2, 3],
  "workspace_id": 1
}
```

**Filter High-Score Leads:**
```bash
GET /api/leads?health_score_min=70&next_action=add_to_campaign
```

## 🎨 UI Recommendations

**Score Display:**
- Use progress bars or color-coded badges
- Show score breakdown in tooltip or expandable section
- Highlight score changes (e.g., "↑ +5 from last week")

**Next Action Display:**
- Use semantic icons and colors
- Make actions clickable (e.g., "Add to campaign" button)
- Show reason in tooltip or expandable section

**Bulk Actions:**
- "Add all 'add_to_campaign' leads to list"
- "Schedule follow-ups for all 'schedule_follow_up' leads"
- "Run enrichment for all 'review_or_enrich' leads"

