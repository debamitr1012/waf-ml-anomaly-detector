# Next.js Dashboard

This is the Next.js TypeScript dashboard for the WAF ML Anomaly Detection system.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Production Build

```bash
npm run build
npm start
```

## Features

- Real-time anomaly monitoring
- Interactive charts and analytics
- Security rule management
- ModSecurity and NGINX rule export
- TypeScript for type safety
- Tailwind CSS for styling
- Chart.js for visualizations

## Default Login

- Username: `admin`
- Password: `changeme`

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Chart.js
- Axios
- date-fns
