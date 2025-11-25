/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002",
  },
  // Optimize for production
  compress: true,
  poweredByHeader: false,
  // Image optimization (if needed)
  images: {
    domains: [],
    unoptimized: false,
  },
};

module.exports = nextConfig;

