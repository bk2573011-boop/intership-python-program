"""Tests for list utility functions (list_programs.py)."""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from list_programs import (  # noqa: E402
    filter_negative,
    filter_positive,
    filter_even,
    filter_odd,
    squares,
    cubes,
    product,
    remove_duplicates,
    average,
)


def test_filter_negative():
    assert filter_negative([10, -5, 20, -15, 30, -25]) == [-5, -15, -25]
    assert filter_negative([1, 2, 3]) == []
    assert filter_negative([]) == []


def test_filter_positive():
    assert filter_positive([-1, 0, 1, 2]) == [1, 2]
    assert filter_positive([]) == []


def test_filter_even_odd():
    data = [1, 2, 3, 4, 5, 6]
    assert filter_even(data) == [2, 4, 6]
    assert filter_odd(data) == [1, 3, 5]


def test_squares_and_cubes():
    assert squares([2, 3, 4]) == [4, 9, 16]
    assert cubes([2, 3, 4]) == [8, 27, 64]
    assert squares([]) == []
    assert cubes([]) == []


def test_product():
    assert product([2, 3, 4]) == 24
    assert product([]) == 1
    assert product([5]) == 5


def test_remove_duplicates_preserves_order():
    assert remove_duplicates([10, 20, 10, 30, 20]) == [10, 20, 30]
    assert remove_duplicates([]) == []


def test_average():
    assert average([10, 20, 30, 40]) == 25.0
    assert average([5]) == 5.0
    with pytest.raises(ValueError):
        average([])
