# Top Performing Segments Implementation

## ✅ What's Been Implemented

### 1. Schemas (`app/schemas/dashboard_segments.py`)

- `SegmentPerformance` - Performance metrics for a single segment
- `TopSegmentsResponse` - Response with time range, metric, and list of segments

### 2. Segment Filtering Service (`app/services/segments_service.py`)

- `apply_segment_filter()` - Applies segment filter criteria to leads queries
- Supports filters: sources, min_score, countries, roles, company_sizes, industries, has_email, tags

### 3. Dashboard Segments Service (`app/services/dashboard_segments_service.py`)

- `get_top_segments()` - Calculates segment performance based on campaign outcomes
- Computes: leads_sent, opened, replied, bounced, open_rate, reply_rate, bounce_rate
- Sorts by reply_rate or open_rate
- Handles both campaign tracking (if CampaignORM exists) and simplified metadata-based tracking

### 4. API Endpoint (`app/api/routes_dashboard_segments.py`)

- `GET /api/dashboard/top-segments` - Returns top performing segments
- Query parameters:
  - `days` (default: 30) - Number of days to look back
  - `metric` (default: "reply_rate") - Sort metric: "reply_rate" or "open_rate"
  - `limit` (default: 5) - Maximum number of segments to return
  - `workspace_id` (optional) - Workspace ID for workspace-scoped segments

## 🔄 Next Steps

### 1. Create Campaign Models (if not exist)

If you don't have campaign tracking yet, create:

```python
# app/core/orm_campaigns.py
class CampaignORM(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    name = Column(String(255))
    sent_at = Column(DateTime(timezone=True))
    # ... other fields

class CampaignLeadORM(Base):
    __tablename__ = "campaign_leads"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    sent = Column(Boolean, default=False)
    opened = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    bounced = Column(Boolean, default=False)
    # ... other fields
```

### 2. Integrate Campaign Outcomes

Update the service to properly track campaign outcomes:
- When emails are sent via campaigns, create `CampaignLeadORM` records
- Update `opened`, `replied`, `bounced` flags when tracking events occur
- Link campaigns to segments (either via segment_id on campaign or via lead matching)

### 3. Frontend Integration

**API Client:**
```typescript
// api/dashboard.ts
export async function getTopSegments(
  days = 30,
  metric: "reply_rate" | "open_rate" = "reply_rate",
  limit = 5
): Promise<TopSegmentsResponse> {
  const { data } = await apiClient.get("/api/dashboard/top-segments", {
    params: { days, metric, limit },
  });
  return data;
}
```

**React Component:**
```tsx
// components/dashboard/TopSegmentsWidget.tsx
export function TopSegmentsWidget() {
  const [stats, setStats] = useState<TopSegmentsResponse | null>(null);
  
  useEffect(() => {
    getTopSegments(30, "reply_rate", 5).then(setStats);
  }, []);
  
  // Render table with segment performance
}
```

### 4. Add Segment Links

Make segment names clickable to:
- View segment's leads (`/segments/{id}/leads`)
- See campaigns that used this segment
- Build new lists/playbooks based on top segments

### 5. Enhanced Metrics

Add more metrics:
- Click-through rate (if tracking link clicks)
- Conversion rate (if tracking conversions)
- Average response time
- Best performing time of day/day of week

## 📊 Usage Example

**Request:**
```bash
GET /api/dashboard/top-segments?days=30&metric=reply_rate&limit=5
```

**Response:**
```json
{
  "time_range_from": "2025-01-01T00:00:00Z",
  "time_range_to": "2025-01-31T23:59:59Z",
  "metric": "reply_rate",
  "segments": [
    {
      "segment_id": 1,
      "segment_name": "US SaaS Founders",
      "leads_sent": 310,
      "opened": 192,
      "replied": 43,
      "bounced": 6,
      "open_rate": 0.6194,
      "reply_rate": 0.1387,
      "bounce_rate": 0.0194
    },
    {
      "segment_id": 2,
      "segment_name": "EU CMOs",
      "leads_sent": 180,
      "opened": 99,
      "replied": 16,
      "bounced": 5,
      "open_rate": 0.5500,
      "reply_rate": 0.0889,
      "bounce_rate": 0.0278
    }
  ]
}
```

## 🎯 Integration Points

**With Segments:**
- Segments become measured ICPs, not just saved filters
- Users can see which ICP definitions actually work

**With Campaigns:**
- Campaign outcomes automatically feed into segment performance
- Link campaigns to segments to track performance

**With Playbooks:**
- Prioritize segments with high reply rate when generating lists
- Add playbook option: "Run only for top 3 segments by reply rate"

**With Dashboard:**
- Add widget to main dashboard
- Show alongside other metrics (total leads, verification rate, etc.)

## ⚠️ Important Notes

1. **Campaign Tracking:** The service works with or without CampaignORM. If campaigns don't exist, it uses simplified metadata-based tracking.

2. **Performance:** For large datasets, consider:
   - Caching results (Redis)
   - Pre-computing segment stats in background jobs
   - Materialized views for segment-lead matching

3. **Time Range:** Default is 30 days, but users can adjust (1-365 days).

4. **Metric Selection:** Users can sort by `reply_rate` or `open_rate` to see different insights.

5. **Workspace Scoping:** If workspace_id is provided, only segments and leads from that workspace are included.

## 🚀 Future Enhancements

- **Segment Comparison:** Compare two segments side-by-side
- **Trend Analysis:** Show how segment performance changes over time
- **Predictive Scoring:** Use ML to predict which segments will perform best
- **A/B Testing:** Track segment performance across different campaign variants
- **Export:** Export segment performance data to CSV/Excel

