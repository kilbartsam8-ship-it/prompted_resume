import re
from typing import Dict, List


class LinkClassifier:
    """
    Classifies resume links into profile, certificate, and other links.
    """

    PROFILE_PATTERNS = {
        "LinkedIn": r"linkedin\.com",
        "GitHub": r"github\.com",
        "Behance": r"behance\.net",
        "PersonalWebsite": r"portfolio|personal|website"
    }

    CERTIFICATE_PATTERNS = [
        r"certificate",
        r"credly",
        r"udemy",
        r"coursera",
        r"docsend"
    ]

    def classify(self, links: List[str]) -> Dict:
        classified = {
            "profile_links": {},
            "certificate_links": [],
            "other_links": []
        }

        for link in links:
            matched = False

            for name, pattern in self.PROFILE_PATTERNS.items():
                if re.search(pattern, link, re.I):
                    classified["profile_links"][name] = link
                    matched = True
                    break

            if not matched:
                if any(re.search(p, link, re.I) for p in self.CERTIFICATE_PATTERNS):
                    classified["certificate_links"].append(link)
                else:
                    classified["other_links"].append(link)

        classified["certificate_links"] = sorted(set(classified["certificate_links"]))
        classified["other_links"] = sorted(set(classified["other_links"]))

        return classified
