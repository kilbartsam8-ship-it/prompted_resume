from Resume.features.Matching.preprocessing.cleaner import TextCleaner


class ResumeParser:
    def single_field_to_text(self, data):
        fields = [
            "classification", "gender", "current_location",
            "preferred_location", "preferred_jobtype",
            "preferred_workmode", "current_ctc",
            "expected_ctc", "notice_period", "total_experience"
        ]
        parts = []
        for f in fields:
            if f in data and data[f] not in [None, "", []]:
                parts.append(f"{f}: {data[f]}")
        return "\n".join(parts)

    def experience_to_text(self, exps):
        lines = []
        for e in exps:
            role = e.get("role", "")
            company = e.get("company", "")
            duration = e.get("Duration", "")
            techs = TextCleaner.list_to_text(e.get("technologies_used"))
            resp = TextCleaner.clean_text(e.get("responsibilities", ""))
            lines.append(f"{role} at {company} ({duration})")
            if techs:
                lines.append(f"Technologies: {techs}")
            if resp:
                lines.append(f"Responsibilities: {resp}")
        return "\n".join(lines)

    def projects_to_text(self, projects):
        lines = []
        for p in projects:
            title = p.get("title", "")
            desc = TextCleaner.clean_text(p.get("description", ""))
            techs = TextCleaner.list_to_text(p.get("technologies_used"))
            lines.append(f"{title}: {desc}")
            if techs:
                lines.append(f"Tech: {techs}")
        return "\n".join(lines)

    def resume_to_text(self, data: dict) -> str:
        parts = []

        parts.append(self.single_field_to_text(data))

        if data.get("summary"):
            parts.append("Summary: " + TextCleaner.clean_text(data["summary"]))

        if data.get("technical_skills"):
            parts.append("Technical skills: " + TextCleaner.list_to_text(data["technical_skills"]))

        if data.get("experience_details"):
            parts.append("Experience:\n" + self.experience_to_text(data["experience_details"]))

        if data.get("projects"):
            parts.append("Projects:\n" + self.projects_to_text(data["projects"]))

        if data.get("languages_known"):
            parts.append("Languages: " + TextCleaner.list_to_text(data["languages_known"]))

        return "\n\n".join(p for p in parts if p)
