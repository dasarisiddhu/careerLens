import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { Toaster } from 'react-hot-toast'
import Lenis from '@studio-freight/lenis'
import './index.css'

function SmoothScroll({ children }) {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smooth: true,
    })

    window.__careerLensLenis = lenis

    function raf(time) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }
    requestAnimationFrame(raf)

    return () => {
      delete window.__careerLensLenis
      lenis.destroy()
    }
  }, [])

  return children
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <SmoothScroll>
          <App />
          <Toaster
            position="bottom-right"
            toastOptions={{
              style: {
                background: '#111010',
                color: '#fafaf9',
                border: '1px solid rgba(217,119,6,0.3)',
                borderRadius: '12px',
                fontSize: '13px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(217,119,6,0.1)',
              },
              success: {
                iconTheme: { primary: '#f59e0b', secondary: '#0a0a0a' },
              },
              error: {
                iconTheme: { primary: '#ef4444', secondary: '#fafaf9' },
              },
            }}
          />
        </SmoothScroll>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)


