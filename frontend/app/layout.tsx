import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "AI Learning OS",
  description: "Graph-based adaptive learning system",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
