-- Migration: 20250101000012
-- Description: Widen the notifications.type CHECK constraint to match the domain
-- notification types the application actually produces. The original constraint
-- (info|success|warning|error|reminder) was stale and caused every notification
-- insert to fail with 23514.

ALTER TABLE public.notifications
    DROP CONSTRAINT valid_notification_type;

ALTER TABLE public.notifications
    ADD CONSTRAINT valid_notification_type CHECK (
        type IN (
            'assignment_reminder',
            'deadline_alert',
            'exam_reminder',
            'pomodoro_finished',
            'daily_briefing',
            'email_sync',
            'ocr_completed',
            'document_processed',
            'ai_recommendation'
        )
    );