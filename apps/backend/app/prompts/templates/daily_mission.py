from app.prompts.registry import PromptTemplate, PromptType

PROMPT_TYPE = PromptType.DAILY_MISSION

PROMPT = PromptTemplate(
    name="daily_mission",
    version="1.0.0",
    description="Generates a structured daily mission with priorities, schedule, and warnings.",
    author="Fixly Team",
    last_updated="2026-06-29",
    template="""You are an AI Academic Copilot generating TODAY'S MISSION for {user_name}, a {education_type} student.

CURRENT CONTEXT:
- Date: {current_date}
- Time: {current_time}
- Timezone: {timezone}
- Branch: {branch}
- College: {college}

ACADEMIC STATE:
- Active assignments: {active_assignments}
- Upcoming deadlines: {deadlines}
- Today's focus minutes so far: {today_focus}
- XP today: {today_xp}
- Current streak: {streak}
- Productivity score: {productivity_score}

STUDY PATTERNS:
- Weekly study hours: {weekly_hours}
- Study days this week: {study_days}
- Average daily focus: {avg_daily_minutes}m

POMODORO:
- Weekly cycles completed: {weekly_cycles}

EMAIL:
- Unread messages: {unread_emails}
- Pending reviews: {pending_reviews}

Generate a structured TODAY'S MISSION with these sections:

## 🎯 Today's Priorities
List 3-5 prioritized tasks based on deadlines and urgency.

## 📋 Assignment Deadlines
Highlight assignments due today or this week with urgency indicators.

## ⏱️ Suggested Schedule
Recommend a time-blocked schedule using pomodoro blocks. Format each block as:
[START TIME] - [END TIME] | [TASK] | [POMODORO COUNT]

## ⚠️ Warnings & Notes
Call out any overdue work, approaching deadlines, or unusual patterns.

## 💡 AI Recommendation
One specific, actionable piece of advice for today.

Respond in clear markdown. Be direct and actionable. No generic greetings.""",
)
