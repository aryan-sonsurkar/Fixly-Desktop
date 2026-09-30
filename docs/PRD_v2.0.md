# FIXLY — PRODUCT REQUIREMENTS DOCUMENT

- **Product:** Fixly
- **Version:** PRD v2.0
- **Status:** Product direction / post-v1.0.10
- **Target market:** Students, initially Indian college/diploma students
- **Platform:** Windows desktop first
- **Core philosophy:** Offline-first, privacy-conscious, AI-assisted student execution
- **Current release:** v1.0.10
- **Primary product question:** *Can Fixly become the place a student goes to decide what to do, understand what they need to learn, and actually finish academic work?*

---

## 1. Executive Summary

Fixly is an AI-powered academic workspace designed to consolidate a student's academic context into one persistent environment.

Instead of treating AI as a chatbot that answers isolated questions, Fixly should understand the student's:
- Coursework
- Documents
- Assignments
- Tasks
- Deadlines
- Study plans
- Learning progress
- Knowledge gaps
- Conversations
- Academic priorities

and use that context to help the student determine:
> **"What should I do now?"**

The long-term product is therefore not an AI tutor. It is:
> **An AI operating layer for student life.**

The AI should be able to understand the student's academic state and operate across Fixly's modules.

---

## 2. The Problem

Current student workflows are fragmented:
- **Google Drive** → PDFs
- **WhatsApp** → Assignment instructions
- **NotebookLM** → Document analysis
- **ChatGPT / Gemini** → Questions
- **Google Calendar** → Deadlines
- **Notion / Notes** → Planning
- **YouTube** → Learning
- **Quizlet / Knowt** → Revision
- **College portal** → Academic information
- **Paper notebook** → Actual planning

The problem is not that students lack tools. The problem is that **the tools don't share context**.

A student might ask Gemini: *"Explain normalization."*
Gemini does not know:
- Their DBMS syllabus
- Tomorrow's exam
- Which topics they've already studied
- How much time they have
- What assignments are pending
- Which concepts they repeatedly fail
- What notes their teacher provided

That creates a second problem: **Decision Fatigue**. Students know they need to study, but don't know:
- What should I study first?
- How much should I study?
- Should I finish this assignment or revise?
- Which topics are actually important?
- I have two hours. What can realistically be completed?

Fixly's opportunity is to connect these decisions.

---

## 3. Market Reality — No Sugarcoating

### 3.1 "AI study assistant" is no longer a moat
Gemini currently offers Student Hub, Study Notebooks, personalized learning plans, personalized quizzes, performance tracking, interactive visualizations, Gemini Live, document uploads, and connected Google apps. Furthermore, Google provides eligible Indian college students 1 year of Google AI Plus at no cost (₹399/month thereafter).

Positioning Fixly as *"an AI tutor for students"* is weak—Google already has one.

### 3.2 "Chat with your PDFs" is also weak
NotebookLM already provides source-grounded conversations, notes, mind maps, and audio/video overviews. Quizlet, Knowt, and Gizmo generate practice tests, study guides, flashcards, quizzes, and voice tutoring directly from student material.

Therefore: **PDF → Summary → Flashcards → Quiz cannot be the product's moat.**

---

## 4. The Actual Opportunity

The opportunity is the layer between all these capabilities:
- **NotebookLM:** Understand sources
- **Quizlet:** Memorize / practice
- **Khanmigo:** Tutoring
- **Gemini:** General AI + personalized learning
- **Knowt:** Study-material generation
- **Fixly:** **Academic Execution.**

Fixly optimizes:
$$\text{Understand situation} \longrightarrow \text{Decide priority} \longrightarrow \text{Learn} \longrightarrow \text{Practice} \longrightarrow \text{Plan} \longrightarrow \text{Execute} \longrightarrow \text{Reassess}$$

---

## 5. Product Thesis

- **Current thesis:** Fixly is an AI-powered student productivity workspace.
- **Proposed thesis:** Fixly is an AI academic workspace that builds a persistent understanding of a student's coursework, workload and learning progress, then uses that context to help them decide what to do, learn it, and finish it.
- **Short version:** **Fixly helps students know what to do next.**

---

## 6. Target User & Personas

### Primary User
College students aged approximately 17–24 (engineering, diploma, computer science, STEM managing multiple subjects and assignments). India is the logical initial market given massive AI learning adoption among students.

### Personas
1. **Persona A — The Overloaded Student:** Has 4–6 subjects, assignments, exams, PDFs, deadlines. *"I have so much shit to do that I don't know where to start."* (Fixly's core persona).
2. **Persona B — The AI-Native Student:** Already uses ChatGPT, Gemini, NotebookLM, YouTube. *"AI is useful, but everything is scattered."* Fixly must eliminate context switching.
3. **Persona C — The Weak Planner:** Understands subjects reasonably well but struggles with consistency, deadlines, prioritization, and procrastination.

---

## 7. Product Principles

1. **AI should not be a separate feature:** AI exists across the product. Not "Open AI Assistant", but "What should I do next?".
2. **Context beats intelligence:** A weaker local model with correct student context is more useful than a powerful general model with zero context.
3. **Action beats conversation:** Interactions result in actions (create task, update planner, generate practice, identify gap, schedule study).
4. **Don't optimize for AI usage:** Optimize for student progress. Solving a problem in 20 seconds without chatting is a win.
5. **Don't build another dashboard:** Reduce cognitive load; don't create another chore to maintain.

---

## 8. Current Product Baseline (v1.0.10)

| Module | Status | Highlights |
|---|---|---|
| Desktop App | Built | Tauri v2, React, TypeScript, Zustand, Tailwind, FastAPI, Python, Supabase, SQLite |
| Authentication | Built | Session persistence, JWT, offline resilience against Supabase outages |
| AI Workspace | Built | Local model inference (Qwen2 0.5B via llama-cpp / Ollama), streaming, Markdown |
| Document System | Built | PDF processing, extraction, grounded chat, summaries, notes, flashcards, quizzes |
| Planner | Partially Built / Hardening Needed | Suffers from AI raw JSON leakage into UI. Needs structured actions converted to app state. |

---

## 9. Architecture & Core Systems (v2.0)

### 9.1 AI Orchestration Layer & Tool Registry
AI transitions from an isolated chat endpoint to an Orchestration Layer operating tools:
- `get_student_context()`
- `get_upcoming_deadlines()`
- `get_course_progress()`
- `search_documents()`
- `create_task()` / `update_task()`
- `create_study_session()`
- `generate_quiz()`
- `start_tutor_session()`
- `get_knowledge_gaps()`

### 9.2 Fixly Context Engine
Maintains persistent student state:
```
Student
 ├── Courses (DBMS, DSU, Maths, etc.)
 │    ├── Syllabus
 │    ├── Notes & Docs
 │    ├── Assignments
 │    ├── Exams
 │    └── Progress
 ├── Tasks & Deadlines
 ├── Study Sessions
 ├── Knowledge Gaps
 └── Learning History
```

### 9.3 Deterministic Tutor State Machine
Tutor does not merely answer questions; it teaches deterministically:
$$\text{INTRO} \to \text{ASSESS} \to \text{TEACH} \to \text{QUESTION} \to \text{EVALUATE} \to \begin{cases} \text{Correct} \to \text{CONFIRM} \to \text{MASTERED} \\ \text{Wrong} \to \text{HINT} \to \text{RETRY} \to \text{EVALUATE} \end{cases}$$

Modes: *Teach Me*, *Hint Me*, *Quiz Me*, *Solve With Me*, *Review My Answer*, *Revise*.

### 9.4 Knowledge Gap Engine
Tracks topic mastery states (`Mastered ✓`, `Struggling ⚠`, `Failed ✗`, `Unassessed ?`) derived from quiz results, tutor sessions, document questions, and repeated errors.

### 9.5 Adaptive Study Planner
Replaces static task lists with dynamic schedules combining:
$$\text{Deadlines} + \text{Exam dates} + \text{Available time} + \text{Effort} + \text{Knowledge gaps} + \text{Course priority}$$

---

## 10. Non-Goals — What Fixly Must NOT Build

- Not another ChatGPT clone
- Not another NotebookLM
- Not another Quizlet
- Not another Notion
- Not another calendar / habit tracker
- Not another generic AI tutor or multi-model wrapper
- No social networks, gamification traps, or virtual avatars
- No mobile apps, marketplaces, or institutional LMS sales until core student retention is proven

---

## 11. North Star & Metrics

- **North Star Metric:** Weekly Active Students Completing Meaningful Academic Actions (completed task, completed study session, completed quiz, mastered concept).
- **Activation Metric:** User adds academic context $\to$ uses AI against context $\to$ completes 1 meaningful action.
- **Retention Metric:** D1, D7, D30 return rate based on academic memory.
- **Key Qualitative Signal:** *"It remembered what I had pending and told me what I should work on."*

---

## 12. Implementation Roadmap & Immediate Priorities

### P0 — Immediate Foundations
1. **Fix Planner Structured Output:** Prevent raw AI JSON display; transform AI outputs into deterministic application state & UI components.
2. **Build Academic Context Model:** Formalize Course $\to$ Syllabus $\to$ Documents $\to$ Tasks $\to$ Deadlines relationships.
3. **AI Context Engine:** Enable AI prompts/services to retrieve comprehensive student context before reasoning.
4. **AI Tool Registry:** Safe, deterministic tool execution layer for AI actions.

### P1 — Core Value & Differentiation
1. **"What should I do now?":** Flagship workflow synthesizing time, exams, gaps, and tasks into an actionable session.
2. **Tutor State Machine:** Guided pedagogical loop (Khanmigo-style step-by-step guidance).
3. **Knowledge Gap Engine:** Persistent concept mastery tracking.
4. **Adaptive Planner:** Workload and gap-driven schedule generation.
