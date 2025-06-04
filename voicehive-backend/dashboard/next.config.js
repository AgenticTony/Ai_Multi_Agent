/** @type {import('next').NextConfig} */
const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Referrer-Policy',
    value: 'origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  },
]

const nextConfig = {
  // React Strict Mode for development
  reactStrictMode: true,
  
  // Enable SWC minification
  swcMinify: true,
  
  // Image optimization
  images: {
    domains: ['localhost', 'voicehive.vercel.app'],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60 * 60 * 24 * 7, // 1 week
  },
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // TypeScript and ESLint configuration
  typescript: {
    ignoreBuildErrors: false,
    tsconfigPath: './tsconfig.json',
  },
  
  eslint: {
    ignoreDuringBuilds: false,
    dirs: ['src'],
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ]
  },
  
  // API rewrites for development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
  
  // Webpack configuration for bundle optimization
  webpack: (config, { isServer }) => {
    // Only run this in production
    if (process.env.NODE_ENV === 'production') {
      // Optimize moment.js locales
      config.plugins.push(
        new (require('next/dist/compiled/webpack/webpack').webpack).IgnorePlugin({
          resourceRegExp: /^moment-locales/,
        })
      )
    }
    return config
  },
  
  // Enable experimental features
  experimental: {
    scrollRestoration: true,
    optimizePackageImports: ['lucide-react'],
  },
  
  // Production optimizations
  productionBrowserSourceMaps: false,
  compress: true,
  poweredByHeader: false,
  generateEtags: true,
  
  // Development settings
  devIndicators: {
    buildActivityPosition: 'bottom-right',
  },
}

module.exports = nextConfig
