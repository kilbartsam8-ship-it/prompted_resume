# Matching/service.py

from Resume.features.Matching.preprocessing.resume_parser import ResumeParser
from Resume.features.Matching.embedding.encoder import Encoder
from Resume.features.Matching.validator.matcher import SemanticMatcher
from Resume.features.Matching.models import JDMatchResult, SemanticMatchResponse


class SemanticMatchingService:
    def __init__(self):
        self.resume_parser = ResumeParser()
        self.encoder = Encoder()
        self.matcher = SemanticMatcher()

    async def match_resume_to_jds(
        self,
        resume_json: dict,
        jd_records: list[dict],  # already cleaned
    ) -> SemanticMatchResponse:

        resume_text = self.resume_parser.resume_to_text(resume_json)
        resume_vec = await self.encoder.encode(resume_text)

        matches = []

        for jd in jd_records:
            jd_text = jd["cleaned_text"]  # ← key change
            jd_vec = await self.encoder.encode(jd_text)

            score = self.matcher.match(resume_vec, jd_vec)

            matches.append(
                JDMatchResult(
                    jd_id=str(jd["id"]),
                    title=jd.get("title", ""),
                    score=score,
                )
            )

        matches.sort(key=lambda x: x.score.final_score, reverse=True)

        return SemanticMatchResponse(
            resume_text=resume_text,
            matches=matches
        )
