import type { AppProps } from 'next/app'
import { QueryClient, QueryClientProvider } from 'react-query'
import { useState } from 'react'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30000, // 30 seconds
        cacheTime: 300000, // 5 minutes
        refetchOnWindowFocus: false,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <Component {...pageProps} />
    </QueryClientProvider>
  )
}