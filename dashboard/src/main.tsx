import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'sonner'
import './index.css'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
      <Toaster
        position="bottom-right"
        theme="dark"
        toastOptions={{
          style: {
            background: 'hsl(0 0% 12%)',
            border: '1px solid hsl(0 0% 20%)',
            color: 'hsl(0 0% 98%)',
          },
        }}
        richColors
        closeButton
      />
    </ErrorBoundary>
  </StrictMode>,
)
