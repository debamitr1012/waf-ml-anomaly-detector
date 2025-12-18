import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WAF ML Anomaly Detection',
  description: 'Machine Learning-powered network anomaly detection for Web Application Firewall',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
