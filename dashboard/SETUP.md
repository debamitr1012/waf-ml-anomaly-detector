# WAF ML Anomaly Detection - Next.js Dashboard Setup

## 🎯 Quick Setup (5 Minutes)

### Step 1: Install Node.js
Make sure you have Node.js 18+ installed:
```bash
node --version  # Should be 18.x or higher
```

If not installed, download from: https://nodejs.org/

### Step 2: Install Dashboard Dependencies
```bash
cd dashboard
npm install
```

### Step 3: Configure Environment
```bash
# Copy example environment file
cp .env.local.example .env.local

# Edit .env.local if needed (default values work for local development)
```

### Step 4: Start the Backend API
In a separate terminal:
```bash
# From project root
python src\main.py
```

### Step 5: Start the Dashboard
```bash
# From dashboard directory
npm run dev
```

### Step 6: Access the Dashboard
Open your browser to: **http://localhost:3000**

**Login with:**
- Username: `admin`
- Password: `changeme`

---

## 🐳 Docker Setup

### Start Everything with Docker Compose
```bash
# From project root
docker-compose up
```

Access:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
dashboard/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard home
│   ├── login/
│   │   └── page.tsx       # Login page
│   ├── analytics/
│   │   └── page.tsx       # Analytics page
│   ├── rules/
│   │   └── page.tsx       # Security rules page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── Navbar.tsx
│   ├── StatsCards.tsx
│   ├── AnomalyChart.tsx
│   ├── AttackDistributionChart.tsx
│   └── AlertsTable.tsx
├── lib/                   # Utilities
│   └── api-client.ts      # API client
├── hooks/                 # Custom hooks
│   └── useWebSocket.ts
├── types/                 # TypeScript types
│   └── index.ts
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── tailwind.config.js     # Tailwind config
└── next.config.js         # Next.js config
```

---

## 🎨 Features

### Dashboard Home (`/`)
- Real-time statistics cards
- Anomaly detection timeline chart
- Attack type distribution chart
- Recent alerts table
- Live connection status indicator

### Analytics Page (`/analytics`)
- Performance metrics (latency, throughput, detection rate)
- Attack types distribution with progress bars
- System status overview
- Detailed metrics breakdown

### Rules Page (`/rules`)
- View generated security rules
- Generate new rules from anomalies
- Export rules in multiple formats:
  - JSON
  - ModSecurity
  - NGINX
- Rule details with severity and confidence

---

## 🔧 Development

### Available Scripts

```bash
# Development server (hot reload)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

### Environment Variables

Create `.env.local`:
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Admin Credentials (demo only)
NEXT_PUBLIC_ADMIN_USERNAME=admin
NEXT_PUBLIC_ADMIN_PASSWORD=changeme
```

---

## 🎯 API Integration

The dashboard communicates with the FastAPI backend via REST API:

### API Client Usage

```typescript
import { apiClient } from '@/lib/api-client';

// Get statistics
const stats = await apiClient.getStatistics();

// Analyze traffic
const result = await apiClient.analyzeTraffic({
  source_ip: '192.168.1.100',
  method: 'GET',
  path: '/api/users'
});

// Generate rules
const rules = await apiClient.generateRules({
  confidence_threshold: 0.7,
  max_rules: 10
});

// Export rules
const exported = await apiClient.exportRules('modsecurity');
```

---

## 🎨 Styling

### Tailwind CSS

The dashboard uses Tailwind CSS for styling. Key features:
- Responsive design (mobile, tablet, desktop)
- Custom color palette matching brand
- Utility-first approach
- Custom animations

### Color Scheme
```css
--primary: #667eea (Purple)
--danger: #dc3545 (Red)
--success: #28a745 (Green)
--warning: #ffc107 (Yellow)
--info: #17a2b8 (Blue)
```

---

## 📊 Charts

### Chart.js Integration

```typescript
import { Chart } from 'chart.js';

// Line chart for anomaly timeline
<AnomalyChart alerts={recentAlerts} />

// Doughnut chart for attack distribution
<AttackDistributionChart stats={stats} />
```

---

## 🔐 Authentication

Current implementation uses simple session-based auth for demo purposes.

### Production Recommendations:
1. Implement JWT-based authentication
2. Add refresh tokens
3. Store credentials securely (not in env vars)
4. Add rate limiting
5. Enable HTTPS only
6. Implement role-based access control (RBAC)

---

## 🚀 Production Deployment

### Build for Production
```bash
npm run build
npm start
```

### Docker Production
```bash
docker build -t waf-ml-dashboard .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1 \
  waf-ml-dashboard
```

### Deployment Platforms
- **Vercel**: Native Next.js hosting (recommended)
- **AWS**: ECS/Fargate or Amplify
- **Azure**: App Service or Static Web Apps
- **Google Cloud**: Cloud Run or App Engine
- **Self-hosted**: Docker + Nginx reverse proxy

---

## 🐛 Troubleshooting

### Dashboard Won't Start
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

### API Connection Error
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS settings in FastAPI backend

### Build Errors
```bash
# Type check
npm run type-check

# Clear Next.js cache
rm -rf .next
npm run build
```

### Port Already in Use
```bash
# Kill process on port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use a different port
npm run dev -- -p 3001
```

---

## 📚 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.0.4 | React framework |
| React | 18.2.0 | UI library |
| TypeScript | 5.3.3 | Type safety |
| Tailwind CSS | 3.4.0 | Styling |
| Chart.js | 4.4.1 | Data visualization |
| Axios | 1.6.2 | HTTP client |
| date-fns | 3.0.6 | Date utilities |
| Lucide React | 0.300.0 | Icons |

---

## 🔄 Migration from Flask

See [MIGRATION.md](./MIGRATION.md) for detailed migration notes from the previous Flask-based dashboard.

---

## 🤝 Contributing

1. Follow TypeScript best practices
2. Use functional components with hooks
3. Maintain type safety (no `any` types)
4. Follow existing code structure
5. Test on multiple browsers
6. Update documentation

---

## 📝 License

Part of the WAF ML Anomaly Detection System
