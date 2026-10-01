// frontend/src/pages/dashboard/Upgrade.jsx
import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, X, Zap, Star, Loader2, ShieldCheck, ArrowRight } from 'lucide-react'
import { api } from '../../services/api'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { GlassCard, Button, Badge } from '../../components/ui'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '')

const FEATURES = [
  { label: 'Resume Analyses', free: '1 only', premium: 'Unlimited' },
  { label: 'Mock Interviews', free: '1 only', premium: 'Unlimited' },
  { label: 'Honest Career Coach Messages', free: '20 messages', premium: 'Unlimited' },
  { label: 'ATS Compatibility Checker', free: false, premium: true },
  { label: 'AI Cover Letter Generator', free: false, premium: true },
  { label: 'Skill Gap Analyzer', free: false, premium: true },
  { label: 'Portfolio Website Generator', free: '4 generations', premium: 'Unlimited' },
  { label: 'Job Match Engine', free: false, premium: true },
  { label: 'GitHub Project Analyzer', free: false, premium: true },
  { label: 'Personalized AI Mentor', free: false, premium: true },
]

function CheckoutForm({ onCancel }) {
  const stripe = useStripe()
  const elements = useElements()
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setSubmitting(true)
    setErrorMessage('')

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/dashboard?payment=success`,
      },
    })

    if (error) {
      setErrorMessage(error.message || 'Payment failed. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 pt-2">
      <PaymentElement id="payment-element" options={{ layout: 'tabs' }} />
      {errorMessage && (
        <p className="text-xs font-semibold text-[#E11D48] text-center">{errorMessage}</p>
      )}
      <button
        type="submit"
        disabled={!stripe || submitting}
        className="w-full flex items-center justify-center gap-2 py-3.5 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
      >
        {submitting ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
        {submitting ? 'Processing Payment...' : 'Pay $5.00 & Upgrade'}
      </button>
      {onCancel && (
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="w-full text-center text-xs font-semibold text-[#64748B] hover:text-[#0B0F19] py-1 transition-colors"
        >
          Cancel
        </button>
      )}
    </form>
  )
}

export default function Upgrade() {
  const [clientSecret, setClientSecret] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleStartCheckout = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.initiatePayment({ provider: 'stripe', plan: 'premium' })
      if (!res.client_secret) {
        throw new Error('No client_secret returned from server.')
      }
      setClientSecret(res.client_secret)
    } catch (e) {
      setError(e.message || 'Could not initiate payment. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Hero Banner */}
      <GlassCard className="p-8 sm:p-10 text-center relative overflow-hidden border-white/95 shadow-glass-lg">
        <div
          className="absolute -top-20 -right-20 w-80 h-80 rounded-full pointer-events-none blur-3xl opacity-60"
          style={{ background: 'radial-gradient(circle, rgba(219, 234, 254, 0.7) 0%, transparent 70%)' }}
        />

        <div className="relative max-w-xl mx-auto space-y-3">
          <Badge sparkle size="sm" className="mx-auto">
            Pro Membership
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[#0B0F19] tracking-tight">
            Upgrade to Premium
          </h1>
          <p className="text-xs sm:text-sm text-[#475569] leading-relaxed">
            Unlock unlimited AI resume optimization, mock interviews, and complete career operating system tools.
          </p>
        </div>
      </GlassCard>

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-2 gap-6 items-stretch">
        {/* Free Plan */}
        <GlassCard className="p-6 sm:p-8 flex flex-col justify-between border-slate-200/90 shadow-glass">
          <div>
            <div className="mb-6">
              <span className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Starter</span>
              <h2 className="text-xl font-bold text-[#0B0F19] mt-1">Free Tier</h2>
              <div className="flex items-baseline gap-1 mt-2">
                <span className="text-4xl font-extrabold text-[#0B0F19]">$0</span>
                <span className="text-xs text-[#64748B]">/month</span>
              </div>
            </div>

            <ul className="space-y-3 mb-8">
              {FEATURES.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-xs">
                  {f.free === false ? (
                    <X size={15} className="text-slate-300 shrink-0" />
                  ) : (
                    <CheckCircle2 size={15} className="text-[#16A34A] shrink-0" />
                  )}
                  <span className={f.free === false ? 'text-[#94A3B8]' : 'text-[#0B0F19] font-medium'}>
                    {f.label}{typeof f.free === 'string' ? ` – ${f.free}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <button
            type="button"
            disabled
            className="w-full py-3 rounded-full border border-slate-200 bg-slate-100/60 text-xs font-bold text-[#64748B] cursor-default"
          >
            Current Plan
          </button>
        </GlassCard>

        {/* Premium Plan */}
        <GlassCard className="p-6 sm:p-8 relative flex flex-col justify-between border-blue-200/90 bg-gradient-to-b from-white via-white to-blue-50/30 shadow-glass-lg">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <span className="bg-[#2563EB] text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-sm">
              Most Popular
            </span>
          </div>

          <div>
            <div className="mb-6">
              <span className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Full Access</span>
              <h2 className="text-xl font-bold text-[#0B0F19] mt-1 flex items-center gap-2">
                <span>Premium Pro</span>
                <Star size={16} className="fill-amber-400 text-amber-400" />
              </h2>
              <div className="flex items-baseline gap-1 mt-2">
                <span className="text-4xl font-extrabold text-[#0B0F19]">$5.00</span>
                <span className="text-xs text-[#64748B]">/month</span>
              </div>
            </div>

            <ul className="space-y-3 mb-8">
              {FEATURES.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-xs">
                  <CheckCircle2 size={15} className="text-[#2563EB] shrink-0" />
                  <span className="text-[#0B0F19] font-semibold">
                    {f.label}{f.premium === true ? '' : ` – ${f.premium}`}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {clientSecret ? (
            <Elements
              stripe={stripePromise}
              options={{
                clientSecret,
                appearance: {
                  theme: 'stripe',
                  variables: {
                    colorPrimary: '#2563EB',
                    colorBackground: '#FFFFFF',
                    colorText: '#0B0F19',
                    colorDanger: '#E11D48',
                    borderRadius: '12px',
                  },
                },
              }}
            >
              <CheckoutForm onCancel={() => setClientSecret('')} />
            </Elements>
          ) : (
            <div>
              {error && (
                <p className="text-xs font-semibold text-[#E11D48] text-center mb-3">{error}</p>
              )}
              <button
                type="button"
                onClick={handleStartCheckout}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3.5 rounded-full bg-[#0B0F19] text-white font-bold text-sm hover:bg-[#1E293B] transition-all shadow-md disabled:opacity-50"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
                {loading ? 'Preparing Checkout...' : 'Upgrade Now – $5.00/mo'}
              </button>
              <p className="text-center text-[11px] text-[#64748B] mt-2.5">
                Cancel anytime · Secure checkout via Stripe
              </p>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
