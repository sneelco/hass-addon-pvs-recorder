"""Helpers shared by the ESS device classes"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)

_warned: set[tuple[str, int]] = set()


def to_enum[E: Enum](enum_cls: type[E], value: int | None) -> E | None:
    """Convert a register value to an enum member

    Returns None (instead of raising ValueError) when the read failed or the device reports a
    value the enum does not know about, logging unknown values once.
    """
    if value is None:
        return None

    try:
        return enum_cls(value)
    except ValueError:
        key = (enum_cls.__name__, value)
        if key not in _warned:
            _warned.add(key)
            msg = f"Unknown {enum_cls.__name__} value {value}, publishing as empty"
            logger.warning(msg)
        return None


def enum_name(member: Enum | None) -> str | None:
    """Name of an enum member, or None"""
    return member.name if member is not None else None
