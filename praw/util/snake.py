"""Contains functions dealing with snake case conversions."""

from __future__ import annotations

import re
from typing import Any

_re_camel_to_snake = re.compile(r"([a-z0-9](?=[A-Z])|[A-Z](?=[A-Z][a-z]))")


def camel_to_snake(name: str) -> str:
    """Convert ``name`` from camelCase to snake_case."""
    if type(name) is not str or not name.islower():
        parts = _re_camel_to_snake.split(name)
        for index in range(1, len(parts), 2):
            parts[index] += "_"
        name = "".join(parts)
    return name.lower()


def snake_case_keys(dictionary: dict[str, Any]) -> dict[str, Any]:
    """Return a new dictionary with keys converted to snake_case.

    :param dictionary: The dict to be corrected.

    """
    return {camel_to_snake(k): v for k, v in dictionary.items()}
