import re


def normalize_card_id(raw: str | None) -> str | None:
    """Normalize user input into canonical Card_id format ID######."""
    if raw is None:
        return None
    cleaned = raw.strip().upper()
    if not cleaned:
        return None

    match = re.fullmatch(r"ID?(\d+)", cleaned)
    if match:
        digits = match.group(1).zfill(6)
        return f"ID{digits}"

    if cleaned.isdigit():
        return f"ID{cleaned.zfill(6)}"

    return cleaned

