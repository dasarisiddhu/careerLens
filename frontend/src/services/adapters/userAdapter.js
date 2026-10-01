import { z } from 'zod'

export const UserSchema = z.object({
  id: z.string().optional().default(''),
  email: z.string().optional().default(''),
  full_name: z.string().nullable().optional().default(''),
  plan: z.string().optional().default('free'),
  credits: z.coerce.number().optional().default(0),
  github_username: z.string().nullable().optional().default(null),
  target_role: z.string().nullable().optional().default(null),
  experience_level: z.string().nullable().optional().default(null),
  bio: z.string().nullable().optional().default(''),
})

export function normalizeUser(raw) {
  if (!raw) {
    return UserSchema.parse({})
  }

  // Handle both wrapped { user: {...} } and direct user object
  const data = raw.user && typeof raw.user === 'object' ? raw.user : raw

  const parsed = UserSchema.safeParse(data)
  if (!parsed.success) {
    console.warn('[userAdapter] schema validation fallback:', parsed.error)
    return UserSchema.parse({})
  }

  // If full_name is empty, fallback gracefully to email prefix
  if (!parsed.data.full_name && parsed.data.email) {
    parsed.data.full_name = parsed.data.email.split('@')[0]
  }

  return parsed.data
}
