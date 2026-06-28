import re
from datetime import date
from typing import Any


def resolve_variables(
    template: str,
    context: dict[str, Any] | None = None,
    kwargs: dict[str, Any] | None = None,
) -> str:
    vars_dict: dict[str, str] = {}

    vars_dict["current_date"] = date.today().isoformat()

    if context:
        profile = context.get("profile", {}) or {}
        subjects = context.get("subjects", []) or []

        vars_dict["user_name"] = str(profile.get("display_name") or profile.get("full_name") or "Student")
        vars_dict["education_type"] = str(profile.get("education_type") or "student")
        vars_dict["branch"] = str(profile.get("branch_stream") or "")
        vars_dict["year"] = str(profile.get("education_year") or "")
        vars_dict["college"] = str(profile.get("college_name") or "")
        subject_names = [s.get("name", "") for s in subjects if s.get("name")]
        vars_dict["subjects"] = ", ".join(subject_names) if subject_names else ""

    if kwargs:
        for k, v in kwargs.items():
            if v is not None:
                vars_dict[k] = str(v)

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        val = vars_dict.get(key)
        return val if val is not None else match.group(0)

    return re.sub(r"\{(\w+)\}", replacer, template)


def count_placeholders(template: str) -> list[str]:
    return re.findall(r"\{(\w+)\}", template)
