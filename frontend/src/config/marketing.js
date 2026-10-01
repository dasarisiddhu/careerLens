// ============================================================
// CareerLens — Marketing Figures & Social Proof Configuration
// Centralized configuration to prevent unverifiable marketing claims (Section 5.2)
// ============================================================

export const MARKETING_CONFIG = {
  // Social proof visibility toggle
  SHOW_SOCIAL_PROOF: true,
  STUDENT_COUNT_LABEL: '10,000+ students',

  // Floating Hero Sample Cards
  HERO_CARDS: {
    atsScore: {
      score: 98,
      max: 100,
      label: 'Great Score!',
      tag: 'Sample result',
    },
    skillGap: {
      count: 3,
      label: '3 areas',
      title: 'Skill Gap',
      tag: 'Sample result',
    },
    jobMatch: {
      percentage: 92,
      label: 'Job Match',
      tag: 'Sample result',
    },
  },

  // Metrics Section ("Trusted by Students Like You")
  METRICS: [
    { value: '10K+', label: 'Active Students', detail: 'Growing daily' },
    { value: '95%', label: 'Positive Feedback', detail: 'Satisfaction rate' },
    { value: '3x', label: 'More Interview Calls', detail: 'Reported average' },
    { value: '25+', label: 'Partner Companies', detail: 'Hiring network' },
  ],

  // Real Experiences / Testimonials
  TESTIMONIALS: [
    {
      name: 'Karthik',
      role: 'CSE Student',
      quote: 'CareerLens helped me improve my resume and I got 3x more interview calls.',
      avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&q=80',
    },
    {
      name: 'Priya',
      role: 'IT Student',
      quote: 'The roadmap is super helpful. I finally know what to learn next.',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=120&q=80',
    },
    {
      name: 'Rohan',
      role: 'Final Year Student',
      quote: 'Simple, clean and actually useful. A must for every student.',
      avatar: 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?auto=format&fit=crop&w=120&q=80',
    },
  ],
}
