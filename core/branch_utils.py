"""Branch nationality helpers."""

INDIA_NAMES = frozenset({"india", "republic of india"})


def is_india_nationality(nationality: str | None) -> bool:
    if not nationality:
        return False
    return nationality.strip().casefold() in INDIA_NAMES


def is_india_branch(branch) -> bool:
    if branch is None:
        return False
    return is_india_nationality(getattr(branch, "nationality", ""))
