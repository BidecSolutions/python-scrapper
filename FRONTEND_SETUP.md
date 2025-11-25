# Frontend Setup Guide

Complete SaaS frontend for Lead Scraper with beautiful animations and real-time updates.

## 🚀 Quick Start

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
# or
pnpm install
```

### 3. Configure Environment

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_API_KEY=your_api_key_here
```

### 4. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── dashboard/             # Dashboard page
│   ├── jobs/                  # Jobs pages
│   │   ├── page.tsx          # Jobs listing
│   │   ├── [id]/page.tsx     # Job detail
│   │   └── new/page.tsx      # Create job
│   ├── leads/                 # Leads listing
│   ├── settings/              # Settings page
│   ├── layout.tsx             # Root layout
│   └── page.tsx               # Redirect to dashboard
├── components/
│   ├── layout/
│   │   └── AppLayout.tsx     # Main app shell (sidebar + topbar)
│   ├── leads/
│   │   ├── LeadRow.tsx       # Lead table row
│   │   └── LeadDetailPanel.tsx # Slide-in detail panel
│   └── ui/                    # Reusable UI components
│       ├── button.tsx
│       └── badge.tsx
└── lib/
    ├── api.ts                 # API client & types
    └── utils.ts               # Utility functions
```

## 🎨 Features Implemented

### ✅ Complete App Shell
- **Sidebar Navigation**: Dashboard, Jobs, Leads, Settings
- **Top Bar**: Organization info, usage stats with animated progress bar
- **Page Transitions**: Smooth fade + slide animations

### ✅ Dashboard Page
- **Stats Cards**: Total leads, monthly count, avg score, AI enriched %
- **Recent Jobs**: Quick overview of recent scraping jobs
- **Animated Entrance**: Cards fade in with stagger

### ✅ Jobs Page
- **Jobs List**: All scraping jobs with status badges
- **Status Animations**: Pulsing glow for running jobs
- **Stats Cards**: Total, running, completed counts
- **Click to Detail**: Navigate to job detail page

### ✅ Job Detail Page
- **Job Information**: Status, lead count, duration, sites crawled
- **Quality Stats**: High/medium/low quality chips
- **Leads Table**: Full leads list with scores and tags
- **Lead Detail Panel**: Click any lead to see full AI-enriched data

### ✅ Leads Page
- **Leads Table**: Name, email, phone, score, tags
- **Quality Chips**: Quick filter by quality level
- **Lead Detail Panel**: Slide-in panel with complete info
- **Hover Effects**: Row lift on hover

### ✅ Create Job Page
- **Form**: Niche, location, max results, max pages
- **Validation**: Required fields, number limits
- **Smooth Submission**: Creates job and redirects to detail

### ✅ Lead Detail Panel
- **Slide Animation**: Smooth spring-based slide from right
- **Staggered Sections**: Sections fade in with delay
- **Complete Data**: All AI-enriched fields displayed
- **Social Links**: Clickable social media links
- **Tech Stack**: CMS, frameworks, widgets
- **AI Notes**: Generated personalization notes

## 🎭 Animations

### Page Transitions
- Fade + slide up/down on route changes
- `AnimatePresence` for smooth exits

### Status Badges
- Pulsing glow for "running" jobs
- Color-coded by status (cyan, amber, emerald, rose)

### Lead Rows
- Hover lift effect (translateY)
- Animated entrance with stagger
- Smooth exit animations

### Lead Detail Panel
- Spring-based slide from right
- Backdrop blur fade-in
- Staggered section animations

### Stats Cards
- Fade in with slight delay
- Smooth number updates

## 🎨 Design System

### Colors
- **Background**: Slate 950 (almost black)
- **Cards**: Slate 900/800 with transparency
- **Primary**: Cyan 400-500
- **Success**: Emerald 400-500
- **Warning**: Amber 400-500
- **Error**: Rose 400-500

### Typography
- **Headings**: Semibold, larger sizes
- **Body**: Regular, smaller sizes
- **Labels**: Small, slate 400

### Spacing
- Consistent gaps: 2, 4, 6, 8
- Padding: 3, 4, 6, 8

### Borders
- Slate 800 borders
- Rounded corners (xl: 12px)

## 🔌 API Integration

The frontend connects to your FastAPI backend automatically.

### API Client (`lib/api.ts`)

```typescript
// List jobs
const jobs = await apiClient.getJobs();

// Get job details
const job = await apiClient.getJob(123);

// Create job
const job = await apiClient.createJob({
  niche: "dentist clinic",
  location: "Karachi",
  max_results: 20,
  max_pages_per_site: 5,
});

// Get leads
const leads = await apiClient.getLeads(jobId, filters);
```

### API Endpoints Used

- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/run-once` - Create new job
- `GET /api/leads` - List leads (with filters)

## 🎯 Next Steps

### Enhancements You Can Add

1. **Real-time Updates**
   - WebSocket for live job status updates
   - Polling for job progress
   - Toast notifications for job completion

2. **Advanced Filtering**
   - Tag filters (multi-select)
   - Score range slider
   - Date range picker
   - City/country dropdowns

3. **Export Features**
   - CSV export button
   - Excel export
   - Filtered export

4. **Analytics Dashboard**
   - Charts (recharts or chart.js)
   - Lead trends over time
   - Source performance
   - Quality distribution

5. **Authentication**
   - Login/signup pages
   - Protected routes
   - User profile

6. **Pagination**
   - Infinite scroll
   - Page-based pagination
   - Load more button

## 🔧 Configuration

### Environment Variables

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8002

# Optional
NEXT_PUBLIC_API_KEY=your_api_key_here
```

### Tailwind Config

Custom colors and animations are configured in `tailwind.config.ts`.

### API URL

Update `NEXT_PUBLIC_API_URL` in `.env.local` to point to your backend.

## 📦 Build for Production

```bash
npm run build
npm start
```

## 🎨 Customization

### Change Colors

Edit `app/globals.css` for theme colors or `tailwind.config.ts` for component colors.

### Adjust Animations

Modify Framer Motion props in components to change animation timing/easing.

### Add Components

Follow the pattern in `components/ui/` for reusable components.

## 🐛 Troubleshooting

### API Connection Issues

- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Ensure backend is running on correct port
- Check CORS settings in backend

### Build Errors

- Run `npm install` again
- Clear `.next` folder: `rm -rf .next`
- Check TypeScript errors: `npm run lint`

## 📚 Documentation

- [Next.js Docs](https://nextjs.org/docs)
- [Framer Motion Docs](https://www.framer.com/motion/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)

---

**Your SaaS frontend is ready!** 🚀

