from datetime import date, timedelta

from app.services.study_scoring import calculate_daily_goal_bonus, get_points, reload_weights


class TestStudyScoring:
    def test_get_points_pomodoro(self) -> None:
        assert get_points("pomodoro") == 10

    def test_get_points_assignment(self) -> None:
        assert get_points("assignment") == 25

    def test_get_points_ai_study(self) -> None:
        assert get_points("ai_study") == 8

    def test_get_points_reading(self) -> None:
        assert get_points("reading") == 5

    def test_get_points_manual(self) -> None:
        assert get_points("manual") == 6

    def test_get_points_email(self) -> None:
        assert get_points("email") == 3

    def test_get_points_ocr(self) -> None:
        assert get_points("ocr") == 4

    def test_get_points_pdf_analysis(self) -> None:
        assert get_points("pdf_analysis") == 7

    def test_get_points_quiz(self) -> None:
        assert get_points("quiz") == 12

    def test_get_points_flashcard(self) -> None:
        assert get_points("flashcard") == 4

    def test_get_points_revision(self) -> None:
        assert get_points("revision") == 15

    def test_get_points_unknown_returns_zero(self) -> None:
        assert get_points("unknown_activity") == 0

    def test_get_points_after_reload(self) -> None:
        reload_weights()
        assert get_points("pomodoro") == 10

    def test_daily_goal_bonus_achieved(self) -> None:
        assert calculate_daily_goal_bonus(50) == 15

    def test_daily_goal_bonus_exceeded(self) -> None:
        assert calculate_daily_goal_bonus(100) == 15

    def test_daily_goal_bonus_not_achieved(self) -> None:
        assert calculate_daily_goal_bonus(0) == 0
        assert calculate_daily_goal_bonus(49) == 0


class TestStreakCalculation:
    def test_empty_streak(self) -> None:
        dates: list[dict[str, str]] = []
        sorted_dates = sorted({d["date"] for d in dates}, reverse=True)

        if not sorted_dates:
            current = 0
            longest = 0
        else:
            today = date.today().isoformat()
            current = 0
            check_date = today
            while check_date in sorted_dates:
                current += 1
                parsed = date.fromisoformat(check_date)
                parsed -= timedelta(days=1)
                check_date = parsed.isoformat()

            longest = 0
            temp = 1
            asc = sorted(sorted_dates)
            for i in range(1, len(asc)):
                prev = date.fromisoformat(asc[i - 1])
                curr = date.fromisoformat(asc[i])
                if (curr - prev).days == 1:
                    temp += 1
                else:
                    longest = max(longest, temp)
                    temp = 1
            longest = max(longest, temp)

        assert current == 0
        assert longest == 0

    def test_streak_with_consecutive_days(self) -> None:
        dates = ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05"]
        sorted_dates = sorted(set(dates))

        temp = 1
        longest = 0
        for i in range(1, len(sorted_dates)):
            prev = date.fromisoformat(sorted_dates[i - 1])
            curr = date.fromisoformat(sorted_dates[i])
            if (curr - prev).days == 1:
                temp += 1
            else:
                longest = max(longest, temp)
                temp = 1
        longest = max(longest, temp)

        assert longest == 5

    def test_streak_with_gaps(self) -> None:
        dates = [
            "2026-06-01", "2026-06-02", "2026-06-03",
            "2026-06-05", "2026-06-06", "2026-06-07", "2026-06-08",
        ]
        sorted_dates = sorted(set(dates))

        temp = 1
        longest = 0
        for i in range(1, len(sorted_dates)):
            prev = date.fromisoformat(sorted_dates[i - 1])
            curr = date.fromisoformat(sorted_dates[i])
            if (curr - prev).days == 1:
                temp += 1
            else:
                longest = max(longest, temp)
                temp = 1
        longest = max(longest, temp)

        assert longest == 4

    def test_single_day_streak(self) -> None:
        dates = ["2026-06-01"]
        sorted_dates = sorted(set(dates))

        temp = 1
        longest = 0
        for i in range(1, len(sorted_dates)):
            prev = date.fromisoformat(sorted_dates[i - 1])
            curr = date.fromisoformat(sorted_dates[i])
            if (curr - prev).days == 1:
                temp += 1
            else:
                longest = max(longest, temp)
                temp = 1
        longest = max(longest, temp)

        assert longest == 1


class TestCalendarGeneration:
    def test_leap_year_days(self) -> None:
        days = []
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        current = start
        while current <= end:
            days.append(current)
            current += timedelta(days=1)
        assert len(days) == 366

    def test_non_leap_year_days(self) -> None:
        days = []
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        current = start
        while current <= end:
            days.append(current)
            current += timedelta(days=1)
        assert len(days) == 365

    def test_calendar_first_day(self) -> None:
        d = date(2026, 1, 1)
        assert d.isoformat() == "2026-01-01"

    def test_calendar_last_day(self) -> None:
        d = date(2026, 12, 31)
        assert d.isoformat() == "2026-12-31"
