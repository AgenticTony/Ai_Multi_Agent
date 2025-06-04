import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

// Initialize font with display swap for better performance
const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: {
    default: 'VoiceHive Dashboard',
    template: '%s | VoiceHive',
  },
  description: 'Real-time monitoring and analytics for VoiceHive AI agents',
  keywords: ['VoiceHive', 'Dashboard', 'Monitoring', 'Analytics', 'AI Agents'],
  authors: [{ name: 'VoiceHive Team' }],
  creator: 'VoiceHive',
  publisher: 'VoiceHive',
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'),
  openGraph: {
    title: 'VoiceHive Dashboard',
    description: 'Real-time monitoring and analytics for VoiceHive AI agents',
    url: '/',
    siteName: 'VoiceHive',
    locale: 'en_US',
    type: 'website',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#ffffff',
  colorScheme: 'light',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable}`} suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body className={`${inter.className} min-h-screen bg-gray-50 antialiased`}>
        {children}
      </body>
    </html>
  )
}
