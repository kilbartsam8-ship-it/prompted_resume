from datetime import datetime
import dateparser
from typing import List, Dict


class DurationParser:
    """
    Parses experience periods and computes human-readable durations.
    """

    def parse_duration(self, period_text: str) -> str:
        if not period_text:
            return ""

        normalized = (
            period_text
            .replace("–", "-")
            .replace("to", "-")
            .replace("\u00A0", " ")
            .strip()
        )

        parts = [p.strip() for p in normalized.split("-")]
        if len(parts) != 2:
            return ""

        start_str, end_str = parts
        start_date = dateparser.parse(start_str)

        if not start_date:
            return ""

        end_str_lower = end_str.lower()
        if end_str_lower in {"present", "current", "now"}:
            end_date = datetime.today()
        else:
            end_date = dateparser.parse(end_str)

        if not end_date:
            return ""

        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months < 0:
            return ""

        years = months // 12
        remaining_months = months % 12

        if years > 0 and remaining_months > 0:
            return f"{years} yr {remaining_months} months"
        elif years > 0:
            return f"{years} yr"
        else:
            return f"{remaining_months} months"

    # -------------------- enrichment helpers --------------------

    def add_durations(self, experiences: List[Dict]) -> List[Dict]:
        """
        Adds a 'Duration' field to each experience entry.
        """
        for exp in experiences:
            period = exp.get("Period", "")
            exp["Duration"] = self.parse_duration(period)
        return experiences
