# CareerLens — API Contract Map & Boundary Analysis

## Overview
This document records every API call the frontend makes, the request payload contract, and every response field the UI reads (including nested and fallback fields). It also flags shape ambiguity risks where the frontend must guard against missing or polymorphically typed data (objects vs arrays, string vs number).

---

### 1. User & Profile (`/api/auth/me`)
- **GET `/api/auth/me`**
  - **Request**: Empty (Bearer token)
  - **Response Fields Read**:
    - `user` (object) or root user object
    - `user.id` (string)
    - `user.email` (string)
    - `user.full_name` (string, fallback to email prefix)
    - `user.plan` (string: `'free'` | `'premium'` | `'pro'`)
    - `user.credits` (number, fallback to 0)
    - `user.github_username` (string | null)
    - `user.target_role` (string | null)
    - `user.experience_level` (string | null)
  - **Shape Hazards**: Sometimes returns wrapped in `{ user: {...} }` and sometimes returns the user object directly. Adapter must unwrap if nested.

- **PUT `/api/auth/me`**
  - **Request**: `{ full_name?, github_username?, target_role?, bio?, experience_level? }`
  - **Response**: Updated user object or `{ success: true, user: {...} }`

---

### 2. Resume Extraction & Analysis (Older System A: `/api/resume/*`)
- **POST `/api/resume/extract-text`**
  - **Request**: `{ pdf_base64: string }`
  - **Response Fields Read**:
    - `text` (string, the extracted plain text)
    - `char_count` (number)
  - **Shape Hazards**: On OCR failure or scanned image, `text` may be empty or missing.

- **POST `/api/resume/analyze`**
  - **Request**: `FormData` with fields `resume` (PDF file), `github_url` (string), `job_role` (string)
  - **Response Fields Read**:
    - `id` (string | number)
    - `overall_score` (number, 0-100)
    - `ats_score` (number, 0-100)
    - `formatting_score` (number)
    - `experience_score` (number)
    - `skills_score` (number)
    - `summary` (string)
    - `strengths` (array of strings | array of objects `{ title, description }`)
    - `weaknesses` / `improvements` (array of strings)
    - `suggestions` (array of strings | array of `{ category, text }`)
    - `skill_gaps` (array of strings)
    - `github_analysis` (object: `{ repos_analyzed, tech_stack, highlights }`)
  - **Shape Hazards**: `strengths` and `suggestions` can arrive as either an array of strings or an array of objects. Normalizer must flatten or uniformize to `{ id, title, description, type }`.

- **GET `/api/resume/history`**
  - **Request**: Empty
  - **Response Fields Read**: Array of historical analyses `[{ id, created_at, overall_score, ats_score, job_role }]`

- **GET `/api/resume/:id`**
  - **Request**: Path param `id`
  - **Response Fields Read**: Full analysis response matching `/api/resume/analyze`

- **POST `/api/resume/ats-check`**
  - **Request**: `{ resume_text: string, job_description: string, resume_pdf?: string }`
  - **Response Fields Read**:
    - `ats_score` / `overall_score` (number)
    - `match_score` (number)
    - `matching_keywords` (array of strings)
    - `missing_keywords` (array of strings)
    - `recommendations` (array of strings)
    - `formatting_feedback` (array of strings | object)

---

### 3. Resume Optimizer (System B: `/api/optimizer/*`)
- **POST `/api/optimizer/analyse`**
  - **Request**: `{ resume_text: string, job_description: string, job_title?: string }`
  - **Response Fields Read**:
    - `overall_score` (number, 0-100)
    - `recruiter_lens` (object):
      - `verdict` (string)
      - `score` (number)
      - `key_strengths` (array of strings)
      - `key_weaknesses` (array of strings)
    - `skill_gap_analysis` (array of `{ skill: string, importance: string, status: string }`)
    - `rejection_diagnosis` (object):
      - `primary_reason` (string)
      - `risk_factors` (array of strings)
    - `ats_checks` (object):
      - `formatting` (string/number)
      - `keyword_density` (string/number)
      - `structure` (string/number)
  - **Shape Hazards**: If Gemini fails to produce JSON, the backend can return partial structures. All sections require fallback defaults.

- **POST `/api/optimizer/`**
  - **Request**: `{ resume_text: string, job_description: string, job_title?: string, target_domain?: string }`
  - **Response Fields Read**:
    - `status` (`'success'` | `'blocked'`)
    - `message` (string)
    - `changes_applied` (array of strings)
    - `bullet_diffs` (array):
      - `section` (string)
      - `original` (string)
      - `optimized` (string)
      - `improvement_reason` (string)
      - `jd_requirement` (string)
      - `safety_reverted` (boolean)
    - `summary` (object):
      - `original` (string)
      - `optimized` (string)
    - `ats_regression` (object):
      - `before_score` (number)
      - `after_score` (number)
      - `status` (string)
    - `skill_provenance` (object):
      - `verified` (array of strings)
      - `added_unverified` (array of strings)

- **POST `/api/optimizer/professional-resume-pdf`**
  - **Request**: JSON body with resume structure
  - **Response**: Binary PDF Blob (`application/pdf`)

---

### 4. Job Match Engine (`/api/job-match/`)
- **POST `/api/job-match/`**
  - **Request**: `{ resume_text: string, preferences?: object }`
  - **Response Fields Read**:
    - `matches` (array):
      - `title` (string)
      - `company` (string)
      - `match_percentage` (number)
      - `matching_skills` (array of strings)
      - `missing_skills` (array of strings)
      - `location` (string)
      - `apply_url` (string)

---

### 5. Chatbot (`/api/chatbot/*`)
- **POST `/api/chatbot/message`**
  - **Request**: `{ content: string, session_id?: string }`
  - **Response Fields Read**:
    - `response` (string)
    - `session_id` (string)
- **GET `/api/chatbot/history`**
  - **Request**: Query `?session_id=...`
  - **Response Fields Read**:
    - `messages` (array of `{ role: 'user' | 'assistant', content: string, timestamp?: string }`)

---

### 6. Mock Interview (`/api/interview/*`)
- **POST `/api/interview/start`**
  - **Request**: `{ role: string, experience_level: string, topic?: string }`
  - **Response Fields Read**:
    - `session_id` (string)
    - `questions` (array of `{ id: string, text: string, category: string }`)
- **POST `/api/interview/evaluate`**
  - **Request**: `{ session_id: string, answers: array of { question_id, transcript } }`
  - **Response Fields Read**:
    - `overall_score` (number)
    - `communication_score` (number)
    - `technical_score` (number)
    - `feedback` (string)
    - `question_reviews` (array)

---

### 7. Industry & Hiring News (`/api/news/*`)
- **GET `/api/news/tech`**
  - **Response Fields Read**: `articles` (array of `{ title, url, source, published_at, summary, image_url }`)
- **GET `/api/news/hiring`**
  - **Response Fields Read**: `trends` / `reports` (array of `{ company, role, location, hiring_status, link }`)

---

### 8. Progress Tracker (`/api/resume/progress`)
- **GET `/api/resume/progress`**
  - **Response Fields Read**: `history` (array of `{ date: string, overall_score: number, ats_score: number, job_role: string }`)

---

### 9. Career Recommendations (`/api/recommendations/`)
- **POST `/api/recommendations/`**
  - **Request**: `{ skills?: string[], current_role?: string, target_role?: string }`
  - **Response Fields Read**:
    - `recommendations` (array of `{ title, description, skills_to_learn: string[], projects: array of { name, description } }`)

---

### 10. Community (`/api/community/*`)
- **GET `/api/community/posts`**
  - **Response Fields Read**: Array of `{ id, user_id, title, content, tags: string[], likes_count: number, comments_count: number, created_at: string, user: { full_name, email } }`
- **POST `/api/community/posts`**: `{ title, content, tags, post_type }`
- **POST `/api/community/posts/:id/like`**: `{ liked: boolean, likes_count: number }`
- **GET `/api/community/likes`**: Array of post IDs liked by user
- **GET `/api/community/posts/:id/comments`**: Array of `{ id, content, created_at, user: { full_name } }`
- **POST `/api/community/comments`**: `{ post_id, content }`

---

### 11. Interview Probability Predictor (`/api/interview-probability/*`)
- **POST `/api/interview-probability/`**
  - **Request**: `{ resume_text: string, target_role: string, company_type?: string }`
  - **Response Fields Read**:
    - `probability_percentage` (number)
    - `strengths` (array of strings)
    - `risk_factors` (array of strings)
    - `recommendations` (array of strings)

---

### 12. Beginner Career Switch (`/api/beginner/roadmap`)
- **POST `/api/beginner/roadmap`**
  - **Request**: `{ current_level: string, target_field: string, hours_per_week: number }`
  - **Response Fields Read**:
    - `weeks` / `milestones` (array of `{ week_number: number, topics: string[], projects: string[], resources: string[] }`)

---

### 13. Portfolio Generator (`/api/portfolio/generate`)
- **POST `/api/portfolio/generate`**
  - **Request**: `FormData` or JSON
  - **Response Fields Read**: `{ html: string, preview_url?: string }`
