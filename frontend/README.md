# LeadFlux AI Frontend

A modern, animated SaaS frontend for the Lead Scraper platform built with Next.js, React, Tailwind CSS, and Framer Motion.

## 🚀 Features

- **Beautiful Dark UI**: Sleek dark theme with subtle animations
- **Real-time Status Updates**: Animated status badges with pulsing effects
- **Smooth Transitions**: Page transitions and micro-interactions
- **Lead Intelligence**: Rich lead detail panels with AI-enriched data
- **Responsive Design**: Works on desktop and mobile

## 📦 Tech Stack

- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- **Tailwind CSS**
- **Framer Motion** (animations)
- **Lucide React** (icons)
- **Axios** (API client)

## 🏃 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
# or
yarn install
# or
pnpm install
```

### 2. Configure Environment

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_API_KEY=your_api_key_here
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Dashboard page
│   ├── jobs/              # Jobs listing & detail
│   ├── leads/             # Leads listing
│   └── layout.tsx         # Root layout
├── components/
│   ├── layout/            # App layout components
│   ├── leads/             # Lead-specific components
│   └── ui/                # Reusable UI components
├── lib/
│   ├── api.ts             # API client & types
│   └── utils.ts           # Utility functions
└── public/                # Static assets
```

## 🎨 Key Components

### AppLayout
Main application shell with:
- Sidebar navigation
- Top bar with usage stats
- Animated page transitions

### JobsPage
Job listing with:
- Real-time status badges
- Animated job rows
- Status indicators (pulsing for running jobs)

### LeadsPage
Lead browser with:
- Quality score pills
- Tag display
- Clickable rows for detail view

### LeadDetailPanel
Slide-in panel showing:
- Complete lead information
- AI-enriched data (services, languages, social links)
- Tech stack
- AI-generated notes

## 🔌 API Integration

The frontend connects to the FastAPI backend via `lib/api.ts`. Make sure your backend is running on `http://localhost:8002` (or update `.env.local`).

### API Endpoints Used

- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/run-once` - Create new job
- `GET /api/leads` - List leads (with filters)

## 🎭 Animations

- **Page Transitions**: Fade + slide on route changes
- **Status Badges**: Pulsing glow for running jobs
- **Lead Rows**: Hover lift effect
- **Detail Panel**: Spring-based slide-in from right
- **List Items**: Staggered fade-in animations

## 🎨 Theme

The app uses a dark theme with:
- Slate backgrounds (950, 900, 800)
- Cyan/emerald accents
- Subtle glows and shadows
- Smooth color transitions

## 📝 Next Steps

1. **Add Authentication**: Implement login/signup pages
2. **Real-time Updates**: Add WebSocket support for live job status
3. **Advanced Filters**: Implement tag, score, and date filters
4. **Export Features**: Add CSV/Excel export buttons
5. **Analytics Dashboard**: Add charts and graphs
6. **Job Scheduling**: Add recurring job support

## 🔧 Development

### Build for Production

```bash
npm run build
npm start
```

### Lint

```bash
npm run lint
```

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

Built with ❤️ for Lead Intelligence

