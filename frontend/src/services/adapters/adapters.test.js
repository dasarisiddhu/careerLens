import { describe, it, expect } from 'vitest'
import {
  normalizeUser,
  normalizeOptimizerAnalysis,
  normalizeOptimizerResult,
  normalizeResumeAnalysis,
  normalizeATSCheck,
  normalizeJobMatch,
  normalizeInterviewStart,
  normalizeInterviewEvaluation,
  normalizeTechNews,
  normalizeHiringNews,
} from './index'

describe('Data Boundary Safety & Contract Adapters', () => {
  describe('User Adapter (normalizeUser)', () => {
    it('normalizes valid full user object', () => {
      const fixture = {
        user: {
          id: 'usr-123',
          email: 'test@careerlens.ai',
          full_name: 'Alex Rivera',
          plan: 'pro',
          credits: 50,
        },
      }
      const user = normalizeUser(fixture)
      expect(user.id).toBe('usr-123')
      expect(user.full_name).toBe('Alex Rivera')
      expect(user.plan).toBe('pro')
      expect(user.credits).toBe(50)
    })

    it('gracefully handles missing name by falling back to email prefix', () => {
      const fixture = {
        email: 'developer@example.com',
        full_name: null,
      }
      const user = normalizeUser(fixture)
      expect(user.full_name).toBe('developer')
      expect(user.credits).toBe(0)
    })

    it('tolerates malformed input without throwing', () => {
      const user = normalizeUser(null)
      expect(user.id).toBe('')
      expect(user.plan).toBe('free')
      expect(user.credits).toBe(0)
    })
  })

  describe('Resume Optimizer Adapter (normalizeOptimizerAnalysis & Result)', () => {
    it('clamps out-of-bound scores to 0-100 range and handles strings as numbers', () => {
      const fixture = {
        overall_score: '145', // Out of bounds string
        recruiter_lens: {
          score: -20, // Negative score
          verdict: 'Ready for Review',
          key_strengths: ['Strong React background'],
          key_weaknesses: { item1: 'Missing cloud exposure' }, // Object instead of array
        },
      }
      const res = normalizeOptimizerAnalysis(fixture)
      expect(res.overall_score).toBe(100)
      expect(res.recruiter_lens.score).toBe(0)
      expect(Array.isArray(res.recruiter_lens.key_weaknesses)).toBe(true)
      expect(res.recruiter_lens.key_weaknesses[0]).toContain('Missing cloud exposure')
    })

    it('handles polymorphically shaped skill_gap_analysis', () => {
      const dictFixture = {
        skill_gap_analysis: {
          Docker: 'Missing',
          Kubernetes: 'Recommended',
        },
      }
      const res = normalizeOptimizerAnalysis(dictFixture)
      expect(res.skill_gap_analysis.length).toBe(2)
      expect(res.skill_gap_analysis[0].skill).toBe('Docker')
      expect(res.skill_gap_analysis[0].status).toBe('Missing')
    })

    it('normalizes optimizer result bullet diffs safely', () => {
      const fixture = {
        status: 'success',
        bullet_diffs: [
          {
            section: 'Experience',
            original: 'Built a web application',
            optimized: 'Engineered high-throughput web application serving 10k users',
            improvement_reason: 'Added quantifiable impact',
          },
        ],
      }
      const res = normalizeOptimizerResult(fixture)
      expect(res.status).toBe('success')
      expect(res.bullet_diffs.length).toBe(1)
      expect(res.bullet_diffs[0].improvement_reason).toBe('Added quantifiable impact')
    })
  })

  describe('Resume Analysis & ATS Check Adapter', () => {
    it('normalizes string-array or object-array strengths/suggestions into clean string lists', () => {
      const fixture = {
        overall_score: '88',
        ats_score: 92,
        strengths: [
          { title: 'Fullstack proficiency', description: 'Deep knowledge of React and Python' },
          'Clear chronological history',
        ],
        suggestions: ['Add GitHub link to header'],
      }
      const res = normalizeResumeAnalysis(fixture)
      expect(res.overall_score).toBe(88)
      expect(res.ats_score).toBe(92)
      expect(res.strengths.length).toBe(2)
      expect(res.strengths[0]).toBe('Fullstack proficiency')
    })

    it('tolerates malformed ATS check responses', () => {
      const res = normalizeATSCheck(null)
      expect(res.ats_score).toBe(70)
      expect(Array.isArray(res.matching_keywords)).toBe(true)
    })
  })

  describe('Job Match & Interview Adapters', () => {
    it('normalizes job matches whether passed as direct array or wrapped in object', () => {
      const directArray = [
        { title: 'Frontend Engineer', company: 'Acme', match_percentage: '94' },
      ]
      const res = normalizeJobMatch(directArray)
      expect(res.matches.length).toBe(1)
      expect(res.matches[0].match_percentage).toBe(94)
      expect(res.matches[0].location).toBe('Remote')
    })

    it('normalizes mock interview start and evaluation gracefully', () => {
      const startRes = normalizeInterviewStart({ questions: ['Tell me about your best project.'] })
      expect(startRes.questions.length).toBe(1)
      expect(startRes.questions[0].text).toBe('Tell me about your best project.')

      const evalRes = normalizeInterviewEvaluation({ overall_score: 85 })
      expect(evalRes.overall_score).toBe(85)
      expect(evalRes.communication_score).toBe(75)
    })
  })

  describe('News Adapters', () => {
    it('normalizes news articles and hiring trends safely', () => {
      const tech = normalizeTechNews({ articles: [{ title: 'AI breakthrough' }] })
      expect(tech.articles.length).toBe(1)
      expect(tech.articles[0].title).toBe('AI breakthrough')

      const hiring = normalizeHiringNews({ trends: [{ company: 'Tech Corp' }] })
      expect(hiring.trends.length).toBe(1)
      expect(hiring.trends[0].company).toBe('Tech Corp')
    })
  })
})
