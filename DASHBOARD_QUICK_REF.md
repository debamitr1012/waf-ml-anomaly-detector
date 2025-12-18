# 🚀 WAF ML Dashboard - Quick Reference

## One-Line Setup

```bash
cd dashboard && npm install && npm run dev
```
**Then open:** http://localhost:3000 (Login: admin/changeme)

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `app/page.tsx` | Main dashboard home |
| `components/Navbar.tsx` | Navigation bar |
| `lib/api-client.ts` | Backend API calls |
| `types/index.ts` | TypeScript interfaces |
| `package.json` | Dependencies |
| `next.config.js` | Next.js config |
| `tailwind.config.js` | Styling config |

---

## 🎯 Pages

| Route | Component | Features |
|-------|-----------|----------|
| `/` | Dashboard Home | Stats cards, charts, alerts table |
| `/login` | Login | Authentication |
| `/analytics` | Analytics | Detailed metrics, performance |
| `/rules` | Rules | Security rule management |

---

## 🛠️ Common Commands

```bash
# Development
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm start            # Start production server
npm run lint         # Lint code
npm run type-check   # Check TypeScript types

# Docker
docker-compose up dashboard    # Start dashboard only
docker-compose up              # Start all services

# Troubleshooting
rm -rf .next node_modules && npm install && npm run dev
```

---

## 🎨 Components

```typescript
// Import and use
import StatsCards from '@/components/StatsCards';
import AnomalyChart from '@/components/AnomalyChart';
import AlertsTable from '@/components/AlertsTable';

<StatsCards stats={statistics} />
<AnomalyChart alerts={recentAlerts} />
<AlertsTable alerts={recentAlerts} />
```

---

## 🔌 API Usage

```typescript
import { apiClient } from '@/lib/api-client';

// Get stats
const stats = await apiClient.getStatistics();

// Analyze
const result = await apiClient.analyzeTraffic(data);

// Generate rules
const rules = await apiClient.generateRules({
  confidence_threshold: 0.7,
  max_rules: 10
});

// Export
const exported = await apiClient.exportRules('modsecurity');
```

---

## 🎨 Tailwind Quick Classes

```tsx
// Cards
className="bg-white rounded-lg shadow-md p-6"

// Buttons
className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"

// Badges
className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800"

// Grid layouts
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
```

---

## 📊 Chart.js Setup

```typescript
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

const config: ChartConfiguration = {
  type: 'line',
  data: { labels, datasets },
  options: { responsive: true }
};

const chart = new Chart(ctx, config);
```

---

## 🔐 Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_ADMIN_USERNAME=admin
NEXT_PUBLIC_ADMIN_PASSWORD=changeme
```

---

## 🐛 Quick Fixes

**Port conflict:**
```bash
npm run dev -- -p 3001
```

**Cache issues:**
```bash
rm -rf .next && npm run dev
```

**API not connecting:**
Check `.env.local` and ensure backend is running on port 8000

**Type errors:**
```bash
npm run type-check
```

---

## 📦 Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Chart.js** - Charts
- **Axios** - HTTP client
- **Lucide React** - Icons

---

## 🎯 URLs

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## ✅ Migration Completed

- ✅ Flask → Next.js
- ✅ Python → TypeScript
- ✅ HTML templates → React components
- ✅ Bootstrap → Tailwind CSS
- ✅ Port 5000 → Port 3000
- ✅ Old files removed
- ✅ Docker updated
- ✅ Docs updated

---

**Full docs:** See `dashboard/SETUP.md` and `NEXTJS_DASHBOARD_COMPLETE.md`
