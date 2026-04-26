// ============================================================
// CareerLens – Auth Context
// File: frontend/src/context/AuthContext.jsx
// ============================================================
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../services/supabase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    const hydrateAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (!active) return

        const sessionUser = session?.user ?? null
        if (!sessionUser) {
          setUser(null)
          return
        }

        try {
          const { data } = await supabase.auth.getUser()
          if (!active) return
          setUser(data?.user || sessionUser)
        } catch {
          if (!active) return
          setUser(sessionUser)
        }
      } catch {
        if (!active) return
        setUser(null)
      } finally {
        if (active) setLoading(false)
      }
    }

    hydrateAuth()

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return

      const sessionUser = session?.user ?? null
      if (!sessionUser) {
        setUser(null)
        return
      }

      // Keep UI responsive immediately, then enrich with full identity metadata.
      setUser(sessionUser)
      supabase.auth.getUser()
        .then(({ data }) => {
          if (!active) return
          if (data?.user) setUser(data.user)
        })
        .catch(() => {})
    })

    return () => {
      active = false
      subscription.unsubscribe()
    }
  }, [])

  const signOut = async () => {
    await supabase.auth.signOut()
    setUser(null)
    setProfile(null)
  }

  return (
    <AuthContext.Provider value={{ user, profile, setProfile, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}


