import './globals.css'

export const metadata = {
  title: 'ZLTTBOTS Production Admin Dashboard',
  description: 'Admin controls for affiliate analytics, TikTok automation, and AI product discovery.'
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
