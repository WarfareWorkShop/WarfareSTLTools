"""Utility functions for scaling Blender objects.

This module purposely keeps the logic pure so it can be unit tested
outside of Blender.  The operators in :mod:`warfare_stl_tools.__init__`
delegate to these helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class ScalePreset:
    """Container describing a scale preset used by the add-on UI."""

    name: str
    ratio: float


# Common war-gaming ratios expressed as "1:N" values.  The ratio attribute
# stores the denominator so ``ScalePreset(name="1:100", ratio=100.0)`` means
# 1 real-world unit equals 100 miniature units.
SCALE_PRESETS: Tuple[ScalePreset, ...] = (
    ScalePreset("1:285", 285.0),
    ScalePreset("1:200", 200.0),
    ScalePreset("1:144", 144.0),
    ScalePreset("1:100", 100.0),
    ScalePreset("1:72", 72.0),
    ScalePreset("1:56", 56.0),
    ScalePreset("1:48", 48.0),
    ScalePreset("1:35", 35.0),
)


def scale_factor_for_height(current_height: float, target_height: float) -> float:
    """Return the scale factor to reach ``target_height`` from ``current_height``.

    ``current_height`` and ``target_height`` are expressed in Blender units
    (meters by default).  A :class:`ValueError` is raised when either input is
    not strictly positive because a non-positive height makes the operation
    undefined.
    """

    if current_height <= 0:
        raise ValueError("current_height must be greater than zero")
    if target_height <= 0:
        raise ValueError("target_height must be greater than zero")
    return target_height / current_height


def scale_factor_from_ratio(source_ratio: float, target_ratio: float) -> float:
    """Return the factor that converts from ``source_ratio`` to ``target_ratio``.

    Ratios are expressed as denominators (for example 100 represents 1:100).
    Scaling from 1:100 to 1:50 requires doubling the miniature, yielding a
    factor of ``100 / 50 == 2``.  Inputs must be positive numbers.
    """

    if source_ratio <= 0 or target_ratio <= 0:
        raise ValueError("scale ratios must be greater than zero")
    return source_ratio / target_ratio


def apply_scale(dimensions: Iterable[float], factor: float) -> Tuple[float, ...]:
    """Scale each component in ``dimensions`` by ``factor``.

    The helper is tolerant to any iterable of numeric values which makes it
    suitable for unit testing and for use with Blender's ``Vector`` objects.
    """

    return tuple(component * factor for component in dimensions)
