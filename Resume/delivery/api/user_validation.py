import re

from fastapi import HTTPException

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")


def verify_user_id(user_id: str) -> str:
    normalized = (user_id or "").strip()
    if not USER_ID_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid user_id. Use 3-64 chars: letters, numbers, underscore, hyphen; "
                "must start with a letter or number."
            ),
        )
    return normalized
