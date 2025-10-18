import math

import pytest

from warfare_stl_tools import scaling


def test_scale_factor_for_height_happy_path():
    assert math.isclose(scaling.scale_factor_for_height(0.02, 0.04), 2.0)


def test_scale_factor_for_height_invalid_inputs():
    with pytest.raises(ValueError):
        scaling.scale_factor_for_height(0.0, 0.01)
    with pytest.raises(ValueError):
        scaling.scale_factor_for_height(0.02, 0.0)


def test_scale_factor_from_ratio():
    assert math.isclose(scaling.scale_factor_from_ratio(100, 50), 2.0)


def test_scale_factor_from_ratio_invalid():
    with pytest.raises(ValueError):
        scaling.scale_factor_from_ratio(-1, 50)
    with pytest.raises(ValueError):
        scaling.scale_factor_from_ratio(100, 0)


def test_apply_scale_generic_iterable():
    result = scaling.apply_scale([1, 2, 3], 0.5)
    assert result == (0.5, 1.0, 1.5)
